"""LangGraph chatbot flow implemented with the new runtime interface."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Iterable, List, Mapping, Optional, Sequence, TYPE_CHECKING

from pydantic import Field, model_validator, ValidationInfo
from typing_extensions import Literal

from athos.config.models import AthosConfig, BaseFlowConfig, ToolFramework, expand_env
from athos.utils.paths import resolve_path, read_text_file
from athos.frameworks.langgraph.base import BaseLangGraphFlow
from athos.frameworks.langgraph.factories import build_model
from athos.frameworks.langgraph.utils.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from athos.frameworks.langgraph.utils.translation import to_langgraph_messages
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.models.metrics import ExecutionMetrics, TokenUsage
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - only for static analysis
    from langchain_core.language_models import BaseLanguageModel


logger = logging.getLogger(__name__)


class LangGraphChatbotFlow(BaseLangGraphFlow):
    """Chatbot flow that produces structured outputs and supports streaming."""

    name = "langgraph_chatbot"
    description = "Simple conversational chatbot using LangGraph"
    config_class = None  # Set after class definition
    framework = ToolFramework.LANGGRAPH
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(
        self,
        model: "BaseLanguageModel",
        system_prompt: Optional[str],
        initial_history: List[BaseMessage],
        full_config: AthosConfig
    ) -> None:
        """Construct a chatbot flow with all dependencies.

        Note: Use the create() classmethod in production.
        This constructor is public to support testing with mocks.

        Args:
            model: LangChain chat model (required)
            system_prompt: Optional system prompt
            initial_history: Pre-seeded conversation messages
            full_config: Full ATHOS configuration
        """
        super().__init__(full_config)
        self.model = model
        self.system_prompt = system_prompt
        self._initial_history = initial_history

    @classmethod
    async def create(
        cls,
        flow_config: "LangGraphChatbotFlowConfig",
        athos_config: AthosConfig
    ) -> Self:
        """Create and fully initialize a chatbot flow.

        Builds the LangChain model and constructs the flow instance.

        Args:
            flow_config: Chatbot-specific configuration
            athos_config: Full ATHOS configuration

        Returns:
            Fully initialized chatbot flow
        """
        # Get model config
        if flow_config.model not in athos_config.models:
            raise ValueError(
                f"Model '{flow_config.model}' not found in configuration"
            )
        model_cfg = athos_config.models[flow_config.model]

        # Build model
        model = build_model(model_cfg)

        # Build initial history
        initial_history = cls._build_initial_history_static(flow_config.initial_history)

        logger.info(
            "Initialized %s with model %s",
            cls.name,
            model.model_name,  # ChatOpenAI guarantees model_name attribute in 1.0+
        )

        # Construct flow with all dependencies
        return cls(
            model=model,
            system_prompt=flow_config.system_prompt,
            initial_history=initial_history,
            full_config=athos_config
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the flow once and return a structured response."""

        messages = self._build_messages(input)
        logger.debug("Invoking LangGraph chatbot with %d messages", len(messages))

        try:
            response = await self._invoke_model(messages)
        except Exception as exc:  # noqa: BLE001 - propagate as structured error output
            logger.error("LangGraph chatbot execution failed: %s", exc)
            return FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "exception_type": type(exc).__name__},
            )

        content = self._extract_response_content(response)

        # Build execution metrics
        metrics = ExecutionMetrics(
            model_name=self.model.model_name if hasattr(self.model, 'model_name') else None,
            step_count=1,
        )

        # Extract token usage from response
        # Try usage_metadata (newer LangChain versions)
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata:
            if isinstance(usage_metadata, Mapping):
                input_tokens = usage_metadata.get("input_tokens", 0) or usage_metadata.get(
                    "prompt_tokens", 0
                )
                output_tokens = usage_metadata.get("output_tokens", 0) or usage_metadata.get(
                    "completion_tokens", 0
                )
            else:
                input_tokens = getattr(usage_metadata, "input_tokens", 0) or getattr(
                    usage_metadata, "prompt_tokens", 0
                )
                output_tokens = getattr(usage_metadata, "output_tokens", 0) or getattr(
                    usage_metadata, "completion_tokens", 0
                )

            if input_tokens or output_tokens:
                metrics.token_usage = TokenUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
        # Try older 'usage' attribute (response_metadata.usage)
        elif hasattr(response, "usage"):
            usage = response.usage
            if usage:
                # Handle different usage formats
                if hasattr(usage, "input_tokens"):
                    # Pydantic model or object with attributes
                    input_tokens = getattr(usage, "input_tokens", 0) or getattr(usage, "prompt_tokens", 0)
                    output_tokens = getattr(usage, "output_tokens", 0) or getattr(usage, "completion_tokens", 0)
                elif isinstance(usage, dict):
                    # Dict format
                    input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                else:
                    input_tokens = 0
                    output_tokens = 0

                if input_tokens or output_tokens:
                    metrics.token_usage = TokenUsage(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )

        # Build metadata from metrics
        metadata = {
            "model": self.model.model_name,  # ChatOpenAI guarantees model_name attribute in 1.0+
        }
        metadata.update(metrics.to_dict())

        return FlowOutput(content=content, metadata=metadata)

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream intermediate responses from the underlying model."""

        messages = self._build_messages(input)
        logger.debug("Streaming LangGraph chatbot with %d messages", len(messages))

        # ChatOpenAI (langchain-openai ~=1.0.0) always supports streaming via astream()
        try:
            async for chunk in self.model.astream(messages):
                chunk_text = self._coerce_chunk_content(chunk)
                if not chunk_text:
                    continue
                yield FlowOutput(
                    content=chunk_text,
                    metadata={"streaming": True, "chunk": True},
                )
        except Exception as exc:  # noqa: BLE001 - surface as structured error
            logger.error("LangGraph chatbot streaming failed: %s", exc)
            yield FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "streaming": True},
            )
            return

        yield FlowOutput(
            content="",
            metadata={
                "streaming": True,
                "chunk": False,
                "final": True,
                "model": self.model.model_name,  # ChatOpenAI guarantees model_name attribute in 1.0+
            },
        )

    async def cleanup(self) -> None:
        """No-op cleanup hook for compatibility."""

        pass

    def _build_messages(self, input: FlowInput) -> List[BaseMessage]:
        """Construct LangGraph messages from session history and the new prompt."""

        messages: List[BaseMessage] = []

        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        if self._initial_history:
            messages.extend(self._initial_history)

        messages.extend(to_langgraph_messages(input.session.get_history()))
        messages.append(HumanMessage(input.message))
        return messages

    @staticmethod
    def _build_initial_history_static(
        entries: Sequence[str]
    ) -> List[BaseMessage]:
        """Convert alternating user/assistant strings into LangChain messages."""

        if not entries:
            return []

        if len(entries) % 2 != 0:
            raise ValueError("initial_history must contain an even number of entries")

        history: List[BaseMessage] = []
        for idx in range(0, len(entries), 2):
            user_text = entries[idx]
            assistant_text = entries[idx + 1]
            history.append(HumanMessage(user_text))
            history.append(AIMessage(assistant_text))

        return history

    async def _invoke_model(self, messages: Sequence[BaseMessage]) -> object:
        """Invoke the underlying model."""

        return await self.model.ainvoke(messages)

    def _extract_response_content(self, response: object) -> str:
        """Extract textual content from a LangChain response payload."""

        if hasattr(response, "content"):
            return getattr(response, "content")
        if isinstance(response, str):
            return response
        raise TypeError(
            f"Unexpected response type from chat model: {type(response)!r}"
        )

    def _coerce_chunk_content(self, chunk: object) -> str:
        """Convert streaming chunks into textual content."""

        if chunk is None:
            return ""

        if isinstance(chunk, str):
            return chunk

        # LangChain ``AIMessageChunk`` instances expose their incremental text via
        # the ``content``/``text`` attributes. When ``output_version='v1'`` is
        # enabled, ``content`` may be a list of "content block" dictionaries.
        content = getattr(chunk, "content", None)
        if isinstance(content, str) and content:
            return content
        if isinstance(content, Iterable) and not isinstance(content, (str, bytes)):
            pieces: List[str] = []
            for item in content:
                if isinstance(item, Mapping):
                    text = item.get("text")
                    if isinstance(text, str):
                        pieces.append(text)
            if pieces:
                return "".join(pieces)

        text = getattr(chunk, "text", None)
        if isinstance(text, str) and text:
            return text

        delta = getattr(chunk, "delta", None)
        if isinstance(delta, str) and delta:
            return delta
        if hasattr(delta, "content"):
            delta_content = getattr(delta, "content")
            if isinstance(delta_content, str) and delta_content:
                return delta_content
            if isinstance(delta_content, Iterable) and not isinstance(delta_content, (str, bytes)):
                pieces: List[str] = []
                for item in delta_content:
                    if isinstance(item, Mapping):
                        text = item.get("text")
                        if isinstance(text, str):
                            pieces.append(text)
                if pieces:
                    return "".join(pieces)

        # For unknown chunk shapes we prefer to omit the data rather than emit
        # noisy ``repr`` strings in the UI. Downstream callers treat an empty
        # string as "no chunk emitted".
        return ""



class LangGraphChatbotFlowConfig(BaseFlowConfig):
    """Configuration schema for :class:`LangGraphChatbotFlow`."""

    type: Literal["langgraph_chatbot"]
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt prepended to every conversation.",
    )
    system_prompt_path: Optional[str] = Field(
        default=None,
        description="Path to a file containing the system prompt.",
    )
    @model_validator(mode='before')
    @classmethod
    def load_system_prompt_from_path(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data

        prompt = data.get('system_prompt')
        prompt_path = data.get('system_prompt_path')

        if prompt and prompt_path:
            raise ValueError('Provide either system_prompt or system_prompt_path, not both')

        if prompt_path:
            expanded = expand_env(prompt_path)
            base_dir = Path(info.context['config_dir']) if info.context and 'config_dir' in info.context else Path.cwd()
            resolved = resolve_path(base_dir, expanded or prompt_path)
            data['system_prompt'] = read_text_file(resolved)

        return data

    initial_history: Sequence[str] = Field(
        default_factory=list,
        description=(
            "Optional alternating sequence of user/assistant messages used to seed"
            " the conversation history."
        ),
    )


# Set config_class after class definition to avoid forward reference issues
LangGraphChatbotFlow.config_class = LangGraphChatbotFlowConfig

# Register using new pattern
register_flow(LangGraphChatbotFlow)


__all__ = [
    "LangGraphChatbotFlow",
    "LangGraphChatbotFlowConfig",
]

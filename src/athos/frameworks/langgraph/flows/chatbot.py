"""LangGraph chatbot flow implemented with the new runtime interface."""

from __future__ import annotations

import logging
from typing import AsyncGenerator, List, Optional, Sequence, TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from athos.config.models import AthosConfig, BaseFlowConfig, ModelConfig, ToolFramework
from athos.frameworks.langgraph.factories import build_model
from athos.frameworks.langgraph.utils.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from athos.frameworks.langgraph.utils.translation import to_langgraph_messages
from athos.interfaces.base_flow import BaseFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - only for static analysis
    from langchain_core.language_models import BaseLanguageModel


logger = logging.getLogger(__name__)


class LangGraphChatbotFlow(BaseFlow):
    """Chatbot flow that produces structured outputs and supports streaming."""

    name = "langgraph_chatbot"
    description = "Simple conversational chatbot using LangGraph"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(self, full_config: Optional[AthosConfig] = None) -> None:
        self._full_config = full_config
        self.model: Optional["BaseLanguageModel"] = None
        self.system_prompt: Optional[str] = None
        self._initial_history: List[BaseMessage] = []

    async def initialize(self, config: BaseFlowConfig) -> None:
        """Load the configured model and static prompts once."""

        if self._full_config is None:
            raise RuntimeError("Athos configuration is required to initialize the flow")

        if not isinstance(config, LangGraphChatbotFlowConfig):
            raise TypeError(
                "LangGraphChatbotFlow requires LangGraphChatbotFlowConfig during initialization"
            )

        model_cfg = self._get_model_config(config.model)
        self.model = build_model(model_cfg)
        self.system_prompt = config.system_prompt
        self._initial_history = self._build_initial_history(config.initial_history)

        logger.info(
            "Initialized %s with model %s",
            self.name,
            getattr(self.model, "model_name", model_cfg.model_id),
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
        metadata = {
            "model": getattr(self.model, "model_name", "unknown"),
        }

        usage = getattr(response, "usage", None)
        if usage is not None:
            metadata["tokens"] = usage

        return FlowOutput(content=content, metadata=metadata)

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream intermediate responses from the underlying model."""

        messages = self._build_messages(input)
        logger.debug("Streaming LangGraph chatbot with %d messages", len(messages))

        if self.model is None:
            raise RuntimeError("Flow not initialized; model is unavailable")

        stream_fn = getattr(self.model, "astream", None)
        if stream_fn is None:
            logger.warning("Model does not support streaming; falling back to execute()")
            yield await self.execute(input)
            return

        accumulated = ""
        try:
            async for chunk in stream_fn(messages):  # type: ignore[call-arg]
                chunk_text = self._coerce_chunk_content(chunk)
                if not chunk_text:
                    continue
                accumulated += chunk_text
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
            content=accumulated,
            metadata={
                "streaming": True,
                "chunk": False,
                "final": True,
                "model": getattr(self.model, "model_name", "unknown"),
            },
        )

    async def cleanup(self) -> None:
        """No-op cleanup hook for compatibility."""

        self.model = None
        self._initial_history = []

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

    def _build_initial_history(
        self, entries: Sequence[str]
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
        """Invoke the underlying model, handling legacy LangChain APIs."""

        if self.model is None:
            raise RuntimeError("Flow not initialized; model is unavailable")

        ainvoke = getattr(self.model, "ainvoke", None)
        if callable(ainvoke):
            return await ainvoke(messages)

        agenerate = getattr(self.model, "agenerate", None)
        if callable(agenerate):
            response = await agenerate([messages])
            generations = getattr(response, "generations", None)
            if generations:
                return generations[0][0].message
            return response

        raise AttributeError("Model does not provide an async invocation method")

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

        if hasattr(chunk, "content") and getattr(chunk, "content"):
            return getattr(chunk, "content")

        delta = getattr(chunk, "delta", None)
        if isinstance(delta, str):
            return delta

        return str(chunk) if chunk is not None else ""

    def _get_model_config(self, model_name: str) -> ModelConfig:
        """Retrieve the model configuration from the global ATHOS config."""

        if self._full_config is None:
            raise RuntimeError("Athos configuration is required to build the model")

        try:
            return self._full_config.models[model_name]
        except KeyError as exc:  # pragma: no cover - validation safeguard
            raise ValueError(
                f"Unknown model '{model_name}' configured for {self.name}"
            ) from exc


class LangGraphChatbotFlowConfig(BaseFlowConfig):
    """Configuration schema for :class:`LangGraphChatbotFlow`."""

    type: Literal["langgraph_chatbot"]
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt prepended to every conversation.",
    )
    initial_history: Sequence[str] = Field(
        default_factory=list,
        description=(
            "Optional alternating sequence of user/assistant messages used to seed"
            " the conversation history."
        ),
    )


def create_langgraph_chatbot_flow(
    cfg: LangGraphChatbotFlowConfig, full_cfg: AthosConfig
) -> LangGraphChatbotFlow:
    """Factory for :class:`LangGraphChatbotFlow`."""

    # The FlowRunner will call ``initialize`` with the same configuration.
    return LangGraphChatbotFlow(full_config=full_cfg)


register_flow(
    "langgraph_chatbot",
    LangGraphChatbotFlowConfig,
    create_langgraph_chatbot_flow,
    framework=ToolFramework.LANGGRAPH,
)


__all__ = [
    "LangGraphChatbotFlow",
    "LangGraphChatbotFlowConfig",
    "create_langgraph_chatbot_flow",
]

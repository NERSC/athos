from typing import Any, ClassVar, List, Optional
from pathlib import Path
import logging

from smolagents import ChatMessage, OpenAIServerModel

from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode
from athos.registry.flow_registry import register_flow

from athos.config.models import AthosConfig, ModelConfig, ToolFramework
from athos.frameworks.smolagents.factories import build_model

logger = logging.getLogger(__name__)


class ChatbotFlow(BaseFlow):
    """Simple chatbot flow without tools; uses session for conversation history."""

    # ===== Class metadata (new pattern) =====
    name: ClassVar[str] = "chatbot"
    description: ClassVar[str] = "SmolAgents conversational chatbot"
    framework: ClassVar[ToolFramework] = ToolFramework.SMOLAGENTS
    supported_modes: ClassVar[List[ExecutionMode]] = [ExecutionMode.SYNC]

    def __init__(
        self,
        model: OpenAIServerModel,
        system_prompt: Optional[str],
        full_config: AthosConfig
    ):
        """
        Construct a chatbot flow with all dependencies.

        Note: Use the create() classmethod in production.
        This constructor is public to support testing with mocks.

        Args:
            model: SmolAgents model (required)
            system_prompt: Optional system prompt
            full_config: Full ATHOS configuration
        """
        self.model = model
        self.system_prompt = system_prompt
        self._full_config = full_config

    @classmethod
    async def create(
        cls,
        flow_config: "ChatbotFlowConfig",
        athos_config: AthosConfig
    ) -> "ChatbotFlow":
        """
        Create and fully initialize a chatbot flow.

        Builds the SmolAgents model and constructs the flow instance.

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

        # Construct flow with all dependencies
        return cls(
            model=model,
            system_prompt=flow_config.system_prompt,
            full_config=athos_config
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """
        Execute the chatbot flow once and return structured output.

        Args:
            input: FlowInput containing message and session

        Returns:
            FlowOutput with chatbot response
        """
        message = input.message
        history = input.session.get_history()

        try:
            response_content = await self._process_message(message, history)
            return FlowOutput(
                content=response_content,
                metadata={
                    "model": self.model.model_id if hasattr(self.model, 'model_id') else "unknown",
                    "history_length": len(history),
                }
            )
        except Exception as e:
            logger.error("Chatbot execution failed: %s", e)
            return FlowOutput(
                content=f"Error: {e}",
                metadata={"error": str(e)}
            )

    async def _process_message(self, message: str, history: List[dict]) -> str:
        """
        Process a message using session history instead of instance state.

        Args:
            message: User message
            history: Conversation history from session

        Returns:
            Assistant response
        """
        # Build messages from session history
        messages = []
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))

        # Add history from session
        for msg in history:
            messages.append(
                ChatMessage(role=msg["role"], content=msg["content"])
            )

        # Add current message
        messages.append(ChatMessage(role="user", content=message))

        # Get response
        response = self.model(messages, stop_sequences=["END"])
        return response.content


# Config and factory ---------------------------------------------------------
from pydantic import Field, model_validator, ValidationInfo
from typing_extensions import Literal

from athos.config.models import BaseFlowConfig, expand_env
from athos.utils.paths import resolve_path, read_text_file


class ChatbotFlowConfig(BaseFlowConfig):
    """Configuration for :class:`ChatbotFlow`."""

    type: Literal["chatbot"]
    model: str = Field(description="Model name reference")
    system_prompt: Optional[str] = Field(default=None)
    system_prompt_path: Optional[str] = Field(default=None)
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

    max_iterations: int = Field(default=10, gt=0)


# Set config_class on the flow class
ChatbotFlow.config_class = ChatbotFlowConfig

# Register using new pattern
register_flow(ChatbotFlow)


__all__ = ["ChatbotFlow", "ChatbotFlowConfig"]

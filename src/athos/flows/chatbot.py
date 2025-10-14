from typing import List, Optional
import logging

from smolagents import OpenAIServerModel, ChatMessage

from athos.flows.base import BaseFlow
from athos.core.flow_registry import register_flow

from athos.config.models import ModelConfig, AthosConfig
from athos.factories import build_model

logger = logging.getLogger(__name__)


class ChatbotFlow(BaseFlow):
    """Simple chatbot flow without tools; maintains conversation history."""

    def __init__(self, model: OpenAIServerModel, system_prompt: Optional[str] = None):
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history: List[ChatMessage] = []

    async def execute(self, input_data: str) -> str:
        return await self.process_message(input_data)

    async def process_message(self, message: str) -> str:
        user_message = ChatMessage(role="user", content=message)
        self.conversation_history.append(user_message)

        try:
            messages = []
            if self.system_prompt:
                messages.append(ChatMessage(role="system", content=self.system_prompt))
            messages.extend(self.conversation_history)
            response = self.model(messages, stop_sequences=["END"])
            assistant_message = ChatMessage(role="assistant", content=response.content)
            self.conversation_history.append(assistant_message)
            return assistant_message.content
        except Exception as e:
            logger.error("Chatbot execution failed: %s", e)
            error_message = ChatMessage(role="assistant", content=f"Error: {e}")
            self.conversation_history.append(error_message)
            return error_message.content


# Config and factory ---------------------------------------------------------
from pydantic import Field
from typing_extensions import Literal
from athos.config.models import BaseFlowConfig


class ChatbotFlowConfig(BaseFlowConfig):
    """Configuration for :class:`ChatbotFlow`."""

    type: Literal["chatbot"]
    model: str = Field(description="Model name reference")
    system_prompt: Optional[str] = Field(default=None)
    max_iterations: int = Field(default=10, gt=0)


def create_chatbot_flow(cfg: ChatbotFlowConfig, full_cfg: AthosConfig) -> ChatbotFlow:
    model_cfg: ModelConfig = full_cfg.models[cfg.model]
    model = build_model(model_cfg)
    return ChatbotFlow(model, cfg.system_prompt)


register_flow("chatbot", ChatbotFlowConfig, create_chatbot_flow)


__all__ = ["ChatbotFlow", "ChatbotFlowConfig", "create_chatbot_flow"]

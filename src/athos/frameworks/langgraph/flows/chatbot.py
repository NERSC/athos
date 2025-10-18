"""Simple LangGraph chatbot flow implementation."""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Sequence, TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from athos.config.models import AthosConfig, BaseFlowConfig, ModelConfig
from athos.frameworks.langgraph.factories import build_model
from athos.interfaces.base_flow import BaseFlow
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - only for static analysis
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.messages import BaseMessage
else:  # pragma: no cover - fallback definitions when optional deps are absent
    BaseLanguageModel = Any  # type: ignore[assignment]
    BaseMessage = Any  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
except Exception:  # pragma: no cover - executed only when langchain is unavailable

    class _BaseMessage:
        """Light-weight stand-in for LangChain message objects."""

        def __init__(self, content: str) -> None:
            self.content = content

        def __repr__(self) -> str:  # pragma: no cover - debug helper only
            return f"{self.__class__.__name__}(content={self.content!r})"

    class HumanMessage(_BaseMessage):
        """Fallback human message type."""

    class AIMessage(_BaseMessage):
        """Fallback AI message type."""

    class SystemMessage(_BaseMessage):
        """Fallback system message type."""


logger = logging.getLogger(__name__)


class LangGraphChatbotFlow(BaseFlow):
    """Minimal chatbot flow backed by a single chat model."""

    def __init__(
        self,
        model: BaseLanguageModel,
        *,
        system_prompt: Optional[str] = None,
        initial_history: Optional[Sequence["BaseMessage"]] = None,
    ) -> None:
        self.model = model
        self._system_message: Optional["BaseMessage"] = (
            SystemMessage(system_prompt) if system_prompt else None
        )
        self._history: List["BaseMessage"] = list(initial_history or [])

    async def execute(self, input_data: str) -> str:
        """Send user input to the chat model and return the response text."""

        conversation: List["BaseMessage"] = []
        if self._system_message is not None:
            conversation.append(self._system_message)

        conversation.extend(self._history)
        user_message = HumanMessage(input_data)
        conversation.append(user_message)

        logger.debug("Invoking LangGraph chatbot model with %d messages", len(conversation))

        try:
            response = await self.model.ainvoke(conversation)
        except AttributeError:  # pragma: no cover - defensive fallback
            # Some language models expose ``agenerate`` instead of ``ainvoke``.
            response = await self.model.agenerate([conversation])
            if hasattr(response, "generations"):
                response = response.generations[0][0].message

        if hasattr(response, "content"):
            reply_text = response.content
            ai_message = response
        elif isinstance(response, str):  # pragma: no cover - unlikely but defensive
            reply_text = response
            ai_message = AIMessage(response)
        else:  # pragma: no cover - defensive guard
            raise TypeError(
                "Unexpected response type from chat model: " f"{type(response)!r}"
            )

        self._history.extend([user_message, ai_message])
        return reply_text

    def close(self) -> None:  # pragma: no cover - flow holds no external resources
        self._history.clear()


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

    model_cfg: ModelConfig = full_cfg.models[cfg.model]
    model = build_model(model_cfg)

    history_messages: List["BaseMessage"] = []
    initial_pairs = list(cfg.initial_history)
    if initial_pairs:
        if len(initial_pairs) % 2 != 0:
            raise ValueError(
                "initial_history must contain an even number of entries"
            )
        for idx in range(0, len(initial_pairs), 2):
            user_text = initial_pairs[idx]
            ai_text = initial_pairs[idx + 1]
            history_messages.append(HumanMessage(user_text))
            history_messages.append(AIMessage(ai_text))

    return LangGraphChatbotFlow(
        model=model,
        system_prompt=cfg.system_prompt,
        initial_history=history_messages,
    )


register_flow(
    "langgraph_chatbot",
    LangGraphChatbotFlowConfig,
    create_langgraph_chatbot_flow,
)


__all__ = [
    "LangGraphChatbotFlow",
    "LangGraphChatbotFlowConfig",
    "create_langgraph_chatbot_flow",
]

"""Compatibility wrapper for flow classes."""
from athos.flows import (
    BaseFlow,
    ChatbotFlow,
    AgentFlow,
    ChatbotFlowConfig,
    AgentFlowConfig,
    create_chatbot_flow,
    create_agent_flow,
)

__all__ = [
    "BaseFlow",
    "ChatbotFlow",
    "AgentFlow",
    "ChatbotFlowConfig",
    "AgentFlowConfig",
    "create_chatbot_flow",
    "create_agent_flow",
]

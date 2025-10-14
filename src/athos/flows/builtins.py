"""Register built-in flow implementations with the registry."""

from athos.core.flow_registry import register_flow
from . import (
    ChatbotFlowConfig,
    create_chatbot_flow,
    AgentFlowConfig,
    create_agent_flow,
)


register_flow("chatbot", ChatbotFlowConfig, create_chatbot_flow)
register_flow("agent", AgentFlowConfig, create_agent_flow)

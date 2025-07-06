from typing import TYPE_CHECKING, List
import logging

from athos.core.flow_registry import register_flow
from athos.core.flows import ChatbotFlow, AgentFlow
from athos.config.models import (
    ChatbotFlowConfig,
    AgentFlowConfig,
    PromptChainFlowConfig,
)

if TYPE_CHECKING:  # pragma: no cover - for type hints
    from athos.core.manager import AthosManager

logger = logging.getLogger(__name__)


def _load_tools(manager: "AthosManager", tool_names: List[str]):
    tools = []
    for name in tool_names:
        logger.info("loading tool %s", name)
        tool_cfg = manager.config.tools[name]
        tools.append(manager._load_tool(name, tool_cfg))
    return tools


def _load_mcp_tools(manager: "AthosManager", mcp_names: List[str], tools: List):
    for mcp_name in mcp_names:
        logger.info("loading MCP server %s", mcp_name)
        mcp_cfg = manager.config.mcp_servers[mcp_name]
        mcp_client = manager._create_mcp_client(mcp_name, mcp_cfg)
        tools.extend(mcp_client.get_tools())


def create_chatbot_flow(cfg: ChatbotFlowConfig, manager: "AthosManager"):
    model = manager._get_or_create_model(cfg.model)
    return ChatbotFlow(model, cfg.system_prompt)


def create_agent_flow(cfg: AgentFlowConfig, manager: "AthosManager"):
    tools = _load_tools(manager, cfg.tools)
    _load_mcp_tools(manager, cfg.mcp_servers, tools)
    model = manager._get_or_create_model(cfg.model)
    return AgentFlow(
        model,
        tools,
        cfg.agent_type.value,
        max_steps=cfg.max_steps,
        verbosity_level=cfg.verbosity_level,
        additional_authorized_imports=cfg.additional_authorized_imports,
    )


def create_prompt_chain_flow(cfg: PromptChainFlowConfig, manager: "AthosManager"):
    raise NotImplementedError


register_flow("chatbot", ChatbotFlowConfig, create_chatbot_flow)
register_flow("agent", AgentFlowConfig, create_agent_flow)
register_flow("prompt_chain", PromptChainFlowConfig, create_prompt_chain_flow)

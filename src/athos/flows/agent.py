from typing import List, Optional
import asyncio
import logging

from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    Tool,
    OpenAIServerModel,
    MCPClient,
)

from athos.flows.base import BaseFlow
from athos.config.models import (
    AgentType,
    ModelConfig,
    ToolConfig,
    MCPServerConfig,
    AthosConfig,
)
from athos.factories import build_model, build_tool, build_mcp_client

logger = logging.getLogger(__name__)


class AgentFlow(BaseFlow):
    """General agent flow supporting multiple agent types."""

    def __init__(
        self,
        model: OpenAIServerModel,
        tools: List[Tool],
        agent_type: str = "code",
        mcp_clients: Optional[List[MCPClient]] = None,
        **agent_kwargs,
    ):
        self._mcp_clients = list(mcp_clients or [])

        # Fetch tools from any provided MCP servers
        for client in self._mcp_clients:
            try:
                tools.extend(client.get_tools())
            except Exception as e:  # pragma: no cover - should not crash on errors
                logger.warning("Failed to retrieve tools from MCP client: %s", e)

        if agent_type == "tool_calling":
            agent_kwargs.pop("additional_authorized_imports", None)
            self.agent = ToolCallingAgent(tools=tools, model=model, **agent_kwargs)
            self.agent_type = agent_type
        else:
            self.agent = CodeAgent(tools=tools, model=model, **agent_kwargs)
            self.agent_type = "code"

    async def execute(self, input_data: str):
        try:
            return await asyncio.to_thread(self.agent.run, input_data)
        except Exception as e:
            logger.error("%s execution failed: %s", self.agent.__class__.__name__, e)
            return f"Error: {e}"

    def close(self) -> None:
        """Disconnect any MCP clients held by this flow."""
        for client in self._mcp_clients:
            try:
                client.disconnect()
                logger.info("Disconnected MCP client")
            except Exception as e:  # pragma: no cover - disconnect failures should not crash
                logger.warning("Error disconnecting MCP client: %s", e)
        self._mcp_clients.clear()


# Config and factory ---------------------------------------------------------
from pydantic import Field
from athos.config.models import BaseFlowConfig
from typing_extensions import Literal


class AgentFlowConfig(BaseFlowConfig):
    type: Literal["agent"]
    model: str
    agent_type: AgentType = AgentType.CODE
    mcp_servers: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    max_steps: int = Field(default=10, gt=0)
    verbosity_level: Optional[int] = Field(default=1)
    additional_authorized_imports: List[str] = Field(default_factory=list)
    instructions: Optional[str] = Field(default=None)


def create_agent_flow(cfg: AgentFlowConfig, full_cfg: AthosConfig) -> AgentFlow:
    tool_instances: List[Tool] = []
    mcp_instances: List[MCPClient] = []
    for name in cfg.tools:
        tool_cfg: ToolConfig = full_cfg.tools[name]
        tool_instances.append(build_tool(tool_cfg))
    for name in cfg.mcp_servers:
        mcp_cfg: MCPServerConfig = full_cfg.mcp_servers[name]
        client = build_mcp_client(name, mcp_cfg)
        mcp_instances.append(client)
    model_cfg: ModelConfig = full_cfg.models[cfg.model]
    model = build_model(model_cfg)
    return AgentFlow(
        model,
        tool_instances,
        cfg.agent_type.value,
        mcp_clients=mcp_instances,
        max_steps=cfg.max_steps,
        verbosity_level=cfg.verbosity_level,
        additional_authorized_imports=cfg.additional_authorized_imports,
        instructions=cfg.instructions,
    )


__all__ = ["AgentFlow", "AgentFlowConfig", "create_agent_flow"]

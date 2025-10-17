"""Skeleton LangGraph ReAct agent flow implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from athos.config.models import (
    AthosConfig,
    BaseFlowConfig,
    MCPServerConfig,
    ModelConfig,
    ToolConfig,
)
from athos.frameworks.langgraph.factories import (
    LangGraphMCPClient,
    build_mcp_client,
    build_model,
    build_tool,
)
from athos.interfaces.base_flow import BaseFlow
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import BaseTool
else:  # pragma: no cover - fallback for runtime without optional deps
    BaseLanguageModel = Any  # type: ignore
    BaseTool = Any  # type: ignore

logger = logging.getLogger(__name__)


class LangGraphReactAgentFlow(BaseFlow):
    """ReAct-style LangGraph agent flow.

    The class currently wires together the configuration pieces required to
    construct a LangGraph flow but defers the actual graph construction to a
    future implementation.
    """

    def __init__(
        self,
        model: BaseLanguageModel,
        tools: Sequence[BaseTool],
        instructions: Optional[str] = None,
        *,
        mcp_clients: Optional[Sequence[LangGraphMCPClient]] = None,
        max_iterations: int = 20,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model = model
        self.tools = list(tools)
        self.instructions = instructions
        self.max_iterations = max_iterations
        self.state: Dict[str, Any] = dict(initial_state or {})
        self._graph = None  # Will be populated once the LangGraph wiring is implemented.
        self._mcp_clients = list(mcp_clients or [])

    async def execute(self, input_data: str) -> Any:
        """Execute the LangGraph agent against ``input_data``.

        The actual LangGraph graph is not yet built, so the method raises a
        ``NotImplementedError`` to signal the missing implementation.
        """

        logger.debug(
            "LangGraph ReAct agent invoked with input: %s. Graph construction pending.",
            input_data,
        )
        raise NotImplementedError(
            "LangGraph ReAct agent execution is not implemented yet."
        )

    def close(self) -> None:
        """Close any MCP client connections held by the flow."""

        for client in self._mcp_clients:
            try:
                client.close()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                logger.debug("Error closing LangGraph MCP client '%s': %s", client.name, exc)
        self._mcp_clients.clear()


class LangGraphReactAgentFlowConfig(BaseFlowConfig):
    """Configuration schema for :class:`LangGraphReactAgentFlow`."""

    type: Literal["langgraph_react_agent"]
    tools: List[str] = Field(default_factory=list)
    mcp_servers: List[str] = Field(default_factory=list)
    instructions: Optional[str] = Field(
        default=None,
        description="Additional instructions injected into the agent context.",
    )
    max_iterations: int = Field(
        default=20,
        gt=0,
        description="Maximum iterations allowed during ReAct execution.",
    )
    initial_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional initial state provided to the LangGraph agent.",
    )


def create_langgraph_react_agent_flow(
    cfg: LangGraphReactAgentFlowConfig, full_cfg: AthosConfig
) -> LangGraphReactAgentFlow:
    """Factory for :class:`LangGraphReactAgentFlow`."""

    tool_instances: List[BaseTool] = []
    mcp_instances: List[LangGraphMCPClient] = []
    combined_instructions: List[str] = []

    if cfg.instructions:
        combined_instructions.append(cfg.instructions)

    for tool_name in cfg.tools:
        tool_cfg: ToolConfig = full_cfg.tools[tool_name]
        tool_instances.append(build_tool(tool_cfg))

    for mcp_name in cfg.mcp_servers:
        mcp_cfg: MCPServerConfig = full_cfg.mcp_servers[mcp_name]
        client = build_mcp_client(mcp_name, mcp_cfg)
        mcp_instances.append(client)
        if mcp_cfg.instructions:
            combined_instructions.append(mcp_cfg.instructions)

    model_cfg: ModelConfig = full_cfg.models[cfg.model]
    model = build_model(model_cfg)

    instructions: Optional[str] = (
        "\n\n".join(combined_instructions) if combined_instructions else None
    )

    return LangGraphReactAgentFlow(
        model=model,
        tools=tool_instances,
        instructions=instructions,
        mcp_clients=mcp_instances,
        max_iterations=cfg.max_iterations,
        initial_state=cfg.initial_state,
    )


register_flow(
    "langgraph_react_agent",
    LangGraphReactAgentFlowConfig,
    create_langgraph_react_agent_flow,
)


__all__ = [
    "LangGraphReactAgentFlow",
    "LangGraphReactAgentFlowConfig",
    "create_langgraph_react_agent_flow",
]

"""LangGraph ReAct agent flow implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from athos.config.models import (
    AthosConfig,
    BaseFlowConfig,
    MCPServerConfig,
    ModelConfig,
    ToolConfig,
    ToolFramework,
)
from athos.frameworks.langgraph.factories import (
    build_mcp_client,
    build_model,
    build_tool,
)
from athos.frameworks.langgraph.utils.messages import (
    BaseMessage,
    HumanMessage,
    coerce_to_messages,
)
from athos.interfaces.base_flow import BaseFlow
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import BaseTool
    from langchain_mcp_adapters.client import MultiServerMCPClient

try:  # pragma: no cover - optional dependency
    from langchain_core.messages import AIMessage
    from langgraph.prebuilt import create_react_agent
except Exception as exc:  # pragma: no cover - executed only when langgraph missing
    create_react_agent = None  # type: ignore[assignment]
    _CREATE_REACT_AGENT_IMPORT_ERROR: Optional[Exception] = exc
else:  # pragma: no cover - executed when dependency is available
    _CREATE_REACT_AGENT_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class LangGraphReactAgentFlow(BaseFlow):
    """ReAct-style LangGraph agent flow."""

    def __init__(
        self,
        model: BaseLanguageModel,
        tools: Sequence[BaseTool],
        instructions: Optional[str] = None,
        *,
        mcp_clients: Optional[Sequence["MultiServerMCPClient"]] = None,
        max_iterations: int = 20,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model = model
        self.tools = list(tools)
        self.instructions = instructions
        self.max_iterations = max_iterations
        self.state: Dict[str, Any] = dict(initial_state or {})
        initial_messages = self.state.pop("messages", None)
        self._messages: List["BaseMessage"] = []
        if initial_messages:
            self._messages.extend(self._coerce_messages(initial_messages))

        self._graph = None  # type: ignore[assignment]
        self._graph_lock = asyncio.Lock()
        self._graph_needs_rebuild = True

        self._mcp_clients = list(mcp_clients or [])
        self._mcp_tool_sync_lock = asyncio.Lock()
        self._mcp_tools_loaded = False

    async def execute(self, input_data: str) -> Any:
        """Execute the LangGraph agent against ``input_data``."""

        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        invocation_state = dict(self.state)
        history = list(self._messages)
        history.append(HumanMessage(input_data))
        invocation_state["messages"] = history

        graph = self._graph
        if graph is None:  # pragma: no cover - defensive guard
            raise RuntimeError("LangGraph agent graph is not available")

        logger.debug(
            "LangGraph ReAct agent invoking graph with %d messages", len(history)
        )

        result_state = await graph.ainvoke(  # type: ignore[attr-defined]
            invocation_state,
            config={"recursion_limit": self.max_iterations},
        )

        self._update_state(result_state)
        return self._extract_response(result_state)

    async def close(self) -> None:
        """Close any MCP client connections held by the flow."""

        for client in self._mcp_clients:
            try:
                # MultiServerMCPClient uses async context manager protocol
                if hasattr(client, '__aexit__'):
                    await client.__aexit__(None, None, None)
                    logger.debug("Closed MCP client connection")
            except Exception:  # pragma: no cover - best-effort cleanup
                logger.debug("Ignoring MCP client close error", exc_info=True)

        self._mcp_clients.clear()

    async def _ensure_mcp_tools_loaded(self) -> None:
        """Ensure tools from connected MCP servers are loaded into the flow."""

        if not self._mcp_clients or self._mcp_tools_loaded:
            return

        async with self._mcp_tool_sync_lock:
            if self._mcp_tools_loaded:
                return

            new_tools_loaded = False
            for client in self._mcp_clients:
                try:
                    tools = await client.get_tools()
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning(
                        "Failed to load tools from LangGraph MCP client: %s", exc
                    )
                    continue
                if tools:
                    self.tools.extend(tools)
                    new_tools_loaded = True

            if new_tools_loaded:
                self._graph_needs_rebuild = True

            self._mcp_tools_loaded = True

    async def _ensure_graph_built(self) -> None:
        """Ensure the underlying LangGraph graph is constructed."""

        if self._graph is not None and not self._graph_needs_rebuild:
            return

        async with self._graph_lock:
            if self._graph is not None and not self._graph_needs_rebuild:
                return

            if create_react_agent is None:
                raise ImportError(
                    "The 'langgraph' package is required to use the LangGraph ReAct agent."
                ) from _CREATE_REACT_AGENT_IMPORT_ERROR

            prompt = self.instructions or None
            self._graph = create_react_agent(self.model, list(self.tools), prompt=prompt)
            self._graph_needs_rebuild = False

    def _coerce_messages(self, messages: Any) -> List["BaseMessage"]:
        """Convert various message payloads into LangChain message objects.

        This is a wrapper around the shared coerce_to_messages utility function.
        """
        return coerce_to_messages(messages)

    def _update_state(self, result_state: Any) -> None:
        """Persist the latest LangGraph state for subsequent invocations."""

        if hasattr(result_state, "model_dump"):
            raw_state = result_state.model_dump()
        elif isinstance(result_state, dict):
            raw_state = dict(result_state)
        else:  # pragma: no cover - defensive guard
            raise TypeError(
                "Unexpected state returned from LangGraph agent: "
                f"{type(result_state)!r}"
            )

        messages = raw_state.get("messages") or []
        self._messages = list(messages)
        raw_state["messages"] = self._messages
        self.state = raw_state

    def _extract_response(self, state: Any) -> Any:
        """Derive the flow response from the LangGraph state."""

        if isinstance(state, dict):
            structured = state.get("structured_response")
        elif hasattr(state, "structured_response"):
            structured = getattr(state, "structured_response")
        else:
            structured = None

        if structured is not None:
            return structured

        messages: Sequence["BaseMessage"]
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        for message in reversed(messages):
            if isinstance(message, AIMessage):
                return message.content

        raise RuntimeError("LangGraph agent did not produce an AI message response")


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
    mcp_instances: List["MultiServerMCPClient"] = []
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
    framework=ToolFramework.LANGGRAPH,
)


__all__ = [
    "LangGraphReactAgentFlow",
    "LangGraphReactAgentFlowConfig",
    "create_langgraph_react_agent_flow",
]

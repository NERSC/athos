"""LangGraph ReAct agent flow with new runtime interface."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from athos.config.models import (
    AthosConfig,
    BaseFlowConfig,
    ToolFramework,
)
from athos.frameworks.langgraph.base import BaseLangGraphFlow
from athos.frameworks.langgraph.factories import (
    build_mcp_client,
    build_model,
    build_tool,
)
from athos.frameworks.langgraph.utils.messages import (
    BaseMessage,
    HumanMessage,
)
from athos.frameworks.langgraph.utils.translation import to_langgraph_messages
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
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
    AIMessage = None  # type: ignore[assignment]
    _CREATE_REACT_AGENT_IMPORT_ERROR: Optional[Exception] = exc
else:  # pragma: no cover - executed when dependency is available
    _CREATE_REACT_AGENT_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class LangGraphReactAgentFlow(BaseLangGraphFlow):
    """ReAct-style agent with tool calling capabilities.

    This flow uses LangGraph's create_react_agent to build an agent that can:
    - Call tools (both regular and MCP-based)
    - Reason about tool results
    - Iterate until finding an answer
    """

    name = "langgraph_react_agent"
    description = "ReAct agent with tool calling using LangGraph"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(self, full_config: Optional[AthosConfig] = None) -> None:
        super().__init__(full_config)
        self.model: Optional["BaseLanguageModel"] = None
        self.tools: List["BaseTool"] = []
        self.instructions: Optional[str] = None
        self.max_iterations: int = 20
        self._graph = None  # type: ignore[assignment]
        self._graph_lock = asyncio.Lock()
        self._graph_needs_rebuild = True
        self._mcp_clients: List["MultiServerMCPClient"] = []
        self._mcp_tool_sync_lock = asyncio.Lock()
        self._mcp_tools_loaded = False

    async def initialize(self, config: BaseFlowConfig) -> None:
        """Initialize the agent with model, tools, and MCP clients."""

        if self._full_config is None:
            raise RuntimeError("ATHOS configuration is required to initialize the flow")

        if not isinstance(config, LangGraphReactAgentFlowConfig):
            raise TypeError(
                "LangGraphReactAgentFlow requires LangGraphReactAgentFlowConfig during initialization"
            )

        # Build model
        model_cfg = self._get_model_config(config.model)
        self.model = build_model(model_cfg)

        # Build regular tools
        for tool_name in config.tools:
            tool_cfg = self._get_tool_config(tool_name)
            tool_instance = build_tool(tool_cfg)
            self.tools.append(tool_instance)

        # Build MCP clients (tools loaded lazily on first execute)
        combined_instructions: List[str] = []
        if config.instructions:
            combined_instructions.append(config.instructions)

        for mcp_name in config.mcp_servers:
            mcp_cfg = self._get_mcp_server_config(mcp_name)
            client = build_mcp_client(mcp_name, mcp_cfg)
            self._mcp_clients.append(client)
            if mcp_cfg.instructions:
                combined_instructions.append(mcp_cfg.instructions)

        self.instructions = (
            "\n\n".join(combined_instructions) if combined_instructions else None
        )
        self.max_iterations = config.max_iterations

        logger.info(
            "Initialized %s with model %s, %d tools, %d MCP servers",
            self.name,
            self.model.model_name,
            len(self.tools),
            len(self._mcp_clients),
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the ReAct agent and return structured output."""

        # Ensure MCP tools are loaded and graph is built
        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        # Build messages from session history + new input
        messages = self._build_messages(input)

        logger.debug(
            "Invoking LangGraph ReAct agent with %d messages, %d tools",
            len(messages),
            len(self.tools),
        )

        # Invoke the graph
        try:
            result_state = await self._graph.ainvoke(  # type: ignore[attr-defined]
                {"messages": messages},
                config={"recursion_limit": self.max_iterations},
            )
        except Exception as exc:
            logger.error("LangGraph ReAct agent execution failed: %s", exc)
            return FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "exception_type": type(exc).__name__},
            )

        # Extract response
        content = self._extract_response(result_state)
        metadata = {
            "model": self.model.model_name,
            "tools_available": len(self.tools),
            "max_iterations": self.max_iterations,
        }

        return FlowOutput(content=content, metadata=metadata)

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream agent execution with intermediate updates.

        Note: LangGraph ReAct agents can emit events for tool calls and reasoning.
        For now, we use astream_events to get incremental updates.
        """

        # Ensure MCP tools are loaded and graph is built
        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        # Build messages
        messages = self._build_messages(input)

        logger.debug(
            "Streaming LangGraph ReAct agent with %d messages, %d tools",
            len(messages),
            len(self.tools),
        )

        accumulated_content = ""
        tool_calls_seen = []

        try:
            # Stream events from the graph
            async for event in self._graph.astream_events(  # type: ignore[attr-defined]
                {"messages": messages},
                config={"recursion_limit": self.max_iterations},
                version="v2",
            ):
                event_type = event.get("event")
                event_name = event.get("name", "")

                # Tool call events
                if event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_calls_seen.append(tool_name)
                    yield FlowOutput(
                        content="",
                        metadata={
                            "streaming": True,
                            "event_type": "tool_call",
                            "tool_name": tool_name,
                            "status_message": f"🔧 Using tool: {tool_name}",
                        },
                    )

                # Model streaming chunks
                elif event_type == "on_chat_model_stream":
                    chunk_data = event.get("data", {})
                    chunk = chunk_data.get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        chunk_text = str(chunk.content)
                        if chunk_text:
                            accumulated_content += chunk_text
                            yield FlowOutput(
                                content=chunk_text,
                                metadata={"streaming": True, "chunk": True},
                            )

        except Exception as exc:
            logger.error("LangGraph ReAct agent streaming failed: %s", exc)
            yield FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "streaming": True},
            )
            return

        # Final output
        yield FlowOutput(
            content=accumulated_content or "Agent completed with no text output.",
            metadata={
                "streaming": True,
                "final": True,
                "model": self.model.model_name,
                "tools_used": tool_calls_seen,
            },
        )

    async def cleanup(self) -> None:
        """Close MCP client connections and clean up resources."""

        for client in self._mcp_clients:
            try:
                # MultiServerMCPClient uses async context manager protocol
                if hasattr(client, "__aexit__"):
                    await client.__aexit__(None, None, None)
                    logger.debug("Closed MCP client connection")
            except Exception:  # pragma: no cover - best-effort cleanup
                logger.debug("Ignoring MCP client close error", exc_info=True)

        self._mcp_clients.clear()
        self.model = None
        self.tools.clear()
        self._graph = None

    def _build_messages(self, input: FlowInput) -> List[BaseMessage]:
        """Build message list from session history + new input."""

        messages: List[BaseMessage] = []

        # Add history from session
        messages.extend(to_langgraph_messages(input.session.get_history()))

        # Add current message
        messages.append(HumanMessage(input.message))

        return messages

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
            self._graph = create_react_agent(
                self.model, list(self.tools), prompt=prompt
            )
            self._graph_needs_rebuild = False

            logger.debug(
                "Built LangGraph ReAct agent graph with %d tools", len(self.tools)
            )

    def _extract_response(self, state: Any) -> str:
        """Extract the agent's response from the LangGraph state."""

        # Try structured_response first (if custom state is used)
        if isinstance(state, dict):
            structured = state.get("structured_response")
        elif hasattr(state, "structured_response"):
            structured = getattr(state, "structured_response")
        else:
            structured = None

        if structured is not None:
            return str(structured)

        # Extract from messages
        messages: Sequence["BaseMessage"]
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        # Find last AI message
        for message in reversed(messages):
            if AIMessage and isinstance(message, AIMessage):
                return str(message.content)

        raise RuntimeError("LangGraph agent did not produce an AI message response")


class LangGraphReactAgentFlowConfig(BaseFlowConfig):
    """Configuration schema for :class:`LangGraphReactAgentFlow`."""

    type: Literal["langgraph_react_agent"]
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names from config.tools to provide to the agent.",
    )
    mcp_servers: List[str] = Field(
        default_factory=list,
        description="List of MCP server names from config.mcp_servers to connect to.",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Additional instructions injected into the agent context.",
    )
    max_iterations: int = Field(
        default=20,
        gt=0,
        description="Maximum iterations allowed during ReAct execution.",
    )


def create_langgraph_react_agent_flow(
    cfg: LangGraphReactAgentFlowConfig, full_cfg: AthosConfig
) -> LangGraphReactAgentFlow:
    """Factory for :class:`LangGraphReactAgentFlow`."""

    # The FlowRunner will call ``initialize`` with the same configuration.
    return LangGraphReactAgentFlow(full_config=full_cfg)


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

"""LangGraph agent flow using LangChain's `create_agent` helper."""

from __future__ import annotations

import asyncio
import logging
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Self,
)

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
from athos.frameworks.langgraph.flows._stream_utils import (
    build_tool_update_outputs,
    coerce_stream_chunk_text,
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
    from langchain.agents import create_agent
    from langchain_core.messages import AIMessage
except Exception as exc:  # pragma: no cover - executed only when langchain missing
    create_agent = None  # type: ignore[assignment]
    AIMessage = None  # type: ignore[assignment]
    _CREATE_AGENT_IMPORT_ERROR: Optional[Exception] = exc
else:  # pragma: no cover - executed when dependency is available
    _CREATE_AGENT_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class LangChainAgentFlow(BaseLangGraphFlow):
    """Agent flow powered by LangChain's :func:`create_agent` helper.

    Much like :class:`LangGraphReactAgentFlow`, this flow wires together
    ATHOS-configured models, tools, and MCP servers. Instead of depending on
    LangGraph's `create_react_agent`, it builds the agent graph using the
    higher-level `langchain.agents.create_agent` factory which offers a
    consistent interface across providers.
    """

    name = "langchain_agent"
    description = "General agent using LangChain create_agent"
    config_class = None  # Set after class definition
    framework = ToolFramework.LANGGRAPH
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(
        self,
        model: "BaseLanguageModel",
        tools: List["BaseTool"],
        mcp_clients: List["MultiServerMCPClient"],
        instructions: Optional[str],
        max_iterations: int,
        full_config: AthosConfig,
    ) -> None:
        """Construct a LangChain create_agent flow with all dependencies."""

        super().__init__(full_config)
        self.model = model
        self.tools = tools
        self._mcp_clients = mcp_clients
        self.instructions = instructions
        self.max_iterations = max_iterations
        self._graph = None  # type: ignore[assignment]
        self._graph_lock = asyncio.Lock()
        self._graph_needs_rebuild = True
        self._mcp_tool_sync_lock = asyncio.Lock()
        self._mcp_tools_loaded = False

    @classmethod
    async def create(
        cls,
        flow_config: "LangChainAgentFlowConfig",
        athos_config: AthosConfig,
    ) -> Self:
        """Create and fully initialize a LangChain create_agent flow."""

        if flow_config.model not in athos_config.models:
            raise ValueError(
                f"Model '{flow_config.model}' not found in configuration"
            )
        model_cfg = athos_config.models[flow_config.model]

        model = build_model(model_cfg)

        tools: List["BaseTool"] = []
        for tool_name in flow_config.tools:
            if tool_name not in athos_config.tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in configuration"
                )
            tool_cfg = athos_config.tools[tool_name]
            tool_instance = build_tool(tool_cfg)
            tools.append(tool_instance)

        mcp_clients: List["MultiServerMCPClient"] = []
        combined_instructions: List[str] = []
        if flow_config.instructions:
            combined_instructions.append(flow_config.instructions)

        for mcp_name in flow_config.mcp_servers:
            if mcp_name not in athos_config.mcp_servers:
                raise ValueError(
                    f"MCP server '{mcp_name}' not found in configuration"
                )
            mcp_cfg = athos_config.mcp_servers[mcp_name]
            client = build_mcp_client(mcp_name, mcp_cfg)
            mcp_clients.append(client)
            if mcp_cfg.instructions:
                combined_instructions.append(mcp_cfg.instructions)

        instructions = (
            "\n\n".join(combined_instructions) if combined_instructions else None
        )

        logger.info(
            "Initialized %s with model %s, %d tools, %d MCP servers",
            cls.name,
            model.model_name,
            len(tools),
            len(mcp_clients),
        )

        return cls(
            model=model,
            tools=tools,
            mcp_clients=mcp_clients,
            instructions=instructions,
            max_iterations=flow_config.max_iterations,
            full_config=athos_config,
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the agent graph and return structured output."""

        logger.info("LangChainAgentFlow.execute message: %s", input.message)

        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        messages = self._build_messages(input)

        logger.info(
            "Invoking LangChain create_agent graph with %d messages, %d tools",
            len(messages),
            len(self.tools),
        )

        try:
            result_state = await self._graph.ainvoke(  # type: ignore[attr-defined]
                {"messages": messages},
                config={"recursion_limit": self.max_iterations},
            )
        except Exception as exc:
            logger.error("LangChain create_agent execution failed: %s", exc)
            return FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "exception_type": type(exc).__name__},
            )

        content = self._extract_response(result_state)
        metadata = {
            "model": self.model.model_name,
            "tools_available": len(self.tools),
            "max_iterations": self.max_iterations,
        }

        return FlowOutput(content=content, metadata=metadata)

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream agent execution with intermediate updates."""

        logger.info("LangChainAgentFlow.stream message: %s", input.message)

        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        messages = self._build_messages(input)

        logger.info(
            "Streaming LangChain create_agent graph with %d messages, %d tools",
            len(messages),
            len(self.tools),
        )

        tool_calls_seen: List[str] = []
        seen_tool_call_ids: Set[str] = set()
        completed_tool_call_ids: Set[str] = set()

        try:
            async for mode, payload in self._graph.astream(  # type: ignore[attr-defined]
                {"messages": messages},
                config={"recursion_limit": self.max_iterations},
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    token, metadata = payload
                    chunk_text = coerce_stream_chunk_text(token)
                    if not chunk_text:
                        continue

                    node_name = None
                    if isinstance(metadata, dict):
                        node_name = metadata.get("langgraph_node") or metadata.get("node")

                    chunk_metadata = {"streaming": True, "chunk": True}
                    if isinstance(node_name, str) and node_name:
                        chunk_metadata["node"] = node_name

                    yield FlowOutput(content=chunk_text, metadata=chunk_metadata)

                elif mode == "updates":
                    for update in build_tool_update_outputs(
                        payload,
                        tool_calls_seen=tool_calls_seen,
                        seen_tool_call_ids=seen_tool_call_ids,
                        completed_tool_call_ids=completed_tool_call_ids,
                    ):
                        yield update

        except Exception as exc:
            logger.error("LangChain create_agent streaming failed: %s", exc)
            yield FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "streaming": True},
            )
            return

        yield FlowOutput(
            content="",
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
                if hasattr(client, "__aexit__"):
                    await client.__aexit__(None, None, None)
                    logger.debug("Closed MCP client connection")
            except Exception:  # pragma: no cover - best-effort cleanup
                logger.debug("Ignoring MCP client close error", exc_info=True)

    def _build_messages(self, input: FlowInput) -> List[BaseMessage]:
        """Build message list from session history + new input."""

        messages: List[BaseMessage] = []
        messages.extend(to_langgraph_messages(input.session.get_history()))
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
        """Ensure the underlying agent graph is constructed."""

        if self._graph is not None and not self._graph_needs_rebuild:
            return

        async with self._graph_lock:
            if self._graph is not None and not self._graph_needs_rebuild:
                return

            if create_agent is None:
                raise ImportError(
                    "The 'langchain' package is required to use the LangChain create_agent flow."
                ) from _CREATE_AGENT_IMPORT_ERROR

            system_prompt = self.instructions or None
            self._graph = create_agent(
                self.model, list(self.tools), system_prompt=system_prompt
            )
            self._graph_needs_rebuild = False

            logger.debug(
                "Built LangChain create_agent graph with %d tools", len(self.tools)
            )

    def _extract_response(self, state: Any) -> str:
        """Extract the agent's response from the resulting state."""

        if isinstance(state, dict):
            structured = state.get("structured_response")
        elif hasattr(state, "structured_response"):
            structured = getattr(state, "structured_response")
        else:
            structured = None

        if structured is not None:
            return str(structured)

        messages: Sequence["BaseMessage"]
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        for message in reversed(messages):
            if AIMessage and isinstance(message, AIMessage):
                return str(message.content)

        raise RuntimeError("LangChain create_agent graph did not produce a response")


class LangChainAgentFlowConfig(BaseFlowConfig):
    """Configuration schema for :class:`LangChainAgentFlow`."""

    type: Literal["langchain_agent"]
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
        description="Maximum iterations allowed during agent execution.",
    )


LangChainAgentFlow.config_class = LangChainAgentFlowConfig

register_flow(LangChainAgentFlow)


__all__ = [
    "LangChainAgentFlow",
    "LangChainAgentFlowConfig",
]

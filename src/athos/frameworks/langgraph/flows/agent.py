"""LangGraph agent flow using LangChain's `create_agent` helper."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, TYPE_CHECKING, Self

from pydantic import Field, model_validator, ValidationInfo
from typing_extensions import Literal

from athos.config.models import (
    AthosConfig,
    BaseFlowConfig,
    ToolFramework,
    expand_env,
)

from athos.utils.paths import resolve_path, read_text_file
from athos.frameworks.langgraph.base import BaseLangGraphFlow
from athos.frameworks.langgraph.factories import (
    build_mcp_client,
    build_model,
    build_tool,
)
from athos.frameworks.langgraph.utils.messages import BaseMessage, HumanMessage
from athos.frameworks.langgraph.utils.metrics import (
    aggregate_token_usage,
    collect_tool_call_names,
)
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.models.message import Message
from athos.registry.flow_registry import register_flow

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.runnables import RunnableConfig
    from langchain_core.tools import BaseTool
    from langchain_mcp_adapters.client import MultiServerMCPClient

try:  # pragma: no cover - optional dependency
    from langchain.agents import create_agent
    from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
    from langgraph.checkpoint.memory import InMemorySaver
except Exception as exc:  # pragma: no cover - executed only when langchain missing
    create_agent = None  # type: ignore[assignment]
    AIMessage = None  # type: ignore[assignment]
    AIMessageChunk = None  # type: ignore[assignment]
    ToolMessage = None  # type: ignore[assignment]
    InMemorySaver = None  # type: ignore[assignment]
    _CREATE_AGENT_IMPORT_ERROR: Optional[Exception] = exc
else:  # pragma: no cover - executed when dependency is available
    _CREATE_AGENT_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class LangChainAgentFlow(BaseLangGraphFlow):
    """Agent flow powered by LangChain's :func:`create_agent` helper.

    This flow wires together ATHOS-configured models, tools, and MCP servers
    using LangChain's ``create_agent`` helper. It provides similar
    capabilities to previous ReAct-based LangGraph flows while relying on the
    unified LangChain abstractions for consistency across providers.
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
        system_prompt: Optional[str],
        max_iterations: int,
        full_config: AthosConfig,
    ) -> None:
        """Construct a LangChain create_agent flow with all dependencies."""

        super().__init__(full_config)
        self.model = model
        self.tools = tools
        self._mcp_clients = mcp_clients
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self._graph = None  # type: ignore[assignment]
        self._graph_lock = asyncio.Lock()
        self._graph_needs_rebuild = True
        self._mcp_tool_sync_lock = asyncio.Lock()
        self._mcp_tools_loaded = False
        self._checkpointer = None  # Will be created in _ensure_graph_built

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
        prompt_sections: List[str] = []
        if flow_config.system_prompt:
            prompt_sections.append(flow_config.system_prompt)

        for mcp_name in flow_config.mcp_servers:
            if mcp_name not in athos_config.mcp_servers:
                raise ValueError(
                    f"MCP server '{mcp_name}' not found in configuration"
                )
            mcp_cfg = athos_config.mcp_servers[mcp_name]
            client = build_mcp_client(mcp_name, mcp_cfg)
            mcp_clients.append(client)
            if mcp_cfg.instructions:
                prompt_sections.append(mcp_cfg.instructions)

        system_prompt = (
            "\n\n".join(prompt_sections) if prompt_sections else None
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
            system_prompt=system_prompt,
            max_iterations=flow_config.max_iterations,
            full_config=athos_config,
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the agent graph and return structured output."""

        logger.info("LangChainAgentFlow.execute message: %s", input.message.content)

        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        # Build config with thread_id from session_id
        config = self._build_langgraph_config(input.session.session_id)

        # Only build new message (checkpoint has history)
        messages = self._build_messages(input)

        logger.info(
            "Invoking LangChain create_agent graph with %d messages (new), thread_id=%s, %d tools",
            len(messages),
            input.session.session_id,
            len(self.tools),
        )

        try:
            result_state = await self._graph.ainvoke(  # type: ignore[attr-defined]
                {"messages": messages},
                config=config,
            )
        except Exception as exc:
            logger.error("LangChain create_agent execution failed: %s", exc)
            return FlowOutput(
                content=f"Error: {exc}",
                metadata={"error": True, "exception_type": type(exc).__name__},
            )

        # Debug logging of the graph state
        if logger.isEnabledFor(logging.DEBUG):
            for message in result_state["messages"]:
                message.pretty_print()

        content = self._extract_response(result_state)
        metadata: Dict[str, Any] = {
            "model": self.model.model_name,
            "tools_available": len(self.tools),
            "max_iterations": self.max_iterations,
            "checkpoint_enabled": True,
            "thread_id": input.session.session_id,
        }

        token_usage = self._extract_token_usage(result_state)
        if token_usage:
            metadata["token_usage"] = token_usage

        tool_calls = self._extract_tool_calls(result_state)
        if tool_calls:
            metadata["tool_calls"] = tool_calls

        return FlowOutput(content=content, metadata=metadata)

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream agent execution with type-aware message handling.

        Uses graph.astream with stream_mode="messages" for token-level streaming.
        Provides informative status messages during tool execution phases.

        **Streaming Phases:**

        1. **Tool Call Initiation**: When the agent decides to call a tool,
           AIMessageChunk messages arrive with `tool_call_chunks` containing
           incremental JSON. We detect the first chunk and yield a status message.

        2. **Tool Execution**: After the model completes tool call arguments,
           a ToolMessage arrives from the 'tools' node with the execution result.
           We yield a completion status message.

        3. **Response Streaming**: The agent generates its final response as
           AIMessageChunk messages with actual text content, streamed token by token.

        **Message Type Handling:**

        - **AIMessageChunk**: Check for tool_call_chunks (tool initiation) or
          actual content (response text). Use chunk_position='last' to detect
          phase transitions.

        - **ToolMessage**: Indicates tool execution completed. Contains tool name
          and result in content field.

        **Metadata Fields:**

        - `streaming`: Always True during streaming
        - `chunk`: True for intermediate chunks, False for status messages
        - `message_type`: Type name (AIMessageChunk, ToolMessage)
        - `node`: LangGraph node name (model, tools)
        - `tool_name`: Name of tool being called/completed
        - `event`: Lifecycle events (tool_call_start, tool_call_complete)
        - `status_message`: Human-readable status text for tool execution events
        - `finish_reason`: 'tool_calls' or 'stop' from final chunks
        - `chunk_position`: 'last' on final chunk in a sequence

        **Note:** Status messages for tool execution are provided via
        `metadata["status_message"]` rather than `content` to keep the Flow
        interface-agnostic. OpenWebUI Pipeline uses status_message for
        displaying progress indicators.

        Args:
            input: Flow input containing user message and session state

        Yields:
            FlowOutput: Streaming chunks with content and rich metadata
        """

        logger.info("LangChainAgentFlow.stream started for message: %s", input.message.content)

        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        # Build config with thread_id from session_id
        config = self._build_langgraph_config(input.session.session_id)

        # Only build new message (checkpoint has history)
        messages = self._build_messages(input)

        logger.info(
            "Streaming LangChain create_agent graph with %d messages (new), thread_id=%s, %d tools",
            len(messages),
            input.session.session_id,
            len(self.tools),
        )
        stream_modes = ["messages", "updates"]
        logger.info("Starting astream with stream_mode=%s", stream_modes)

        # Track whether we've emitted thinking status
        thinking_emitted = False
        token_usage: Optional[Dict[str, int]] = None
        tool_names: List[str] = []

        try:
            async for stream_mode, chunk in self._graph.astream(  # type: ignore[attr-defined]
                {"messages": messages},
                config=config,
                stream_mode=stream_modes,
            ):
                if stream_mode == "messages":
                    # Chunk is a tuple: (message, metadata)
                    message, metadata = chunk
                    node_name = metadata.get("langgraph_node", "")
                    message_type = type(message).__name__

                    # Debug: log all message types we receive
                    # logger.info(
                    #     "Received %s from node=%s, has_tool_call_chunks=%s, has_content=%s",
                    #     message_type,
                    #     node_name,
                    #     hasattr(message, "tool_call_chunks") and bool(message.tool_call_chunks),
                    #     hasattr(message, "content") and bool(message.content)
                    # )

                    # === Handle AIMessageChunk (model output) ===
                    if AIMessageChunk and isinstance(message, AIMessageChunk):
                        if not thinking_emitted:
                            thinking_emitted = True
                            status_output = FlowOutput(
                                content="",
                                metadata={
                                    "streaming": True,
                                    "chunk": False,
                                    "message_type": message_type,
                                    "node": node_name,
                                    "event_type": "thinking",
                                    "status_message": "🤔 Thinking...",
                                },
                            )
                            logger.info(
                                "Yielding thinking status: content=%r, metadata=%s",
                                status_output.content,
                                status_output.metadata,
                            )
                            yield status_output

                        # Check for actual text content (agent response)
                        # Content is streamed token by token
                        if hasattr(message, "content") and message.content:
                            content = str(message.content)
                            # Build metadata for this chunk
                            chunk_meta: Dict[str, Any] = {
                                "streaming": True,
                                "chunk": True,
                                "message_type": message_type,
                                "node": node_name,
                            }

                            # Include finish_reason if present (indicates final chunk)
                            if hasattr(message, "response_metadata"):
                                finish_reason = message.response_metadata.get(
                                    "finish_reason"
                                )
                                if finish_reason:
                                    chunk_meta["finish_reason"] = finish_reason

                            # Include chunk_position marker ('last' indicates end)
                            if hasattr(message, "chunk_position"):
                                chunk_meta["chunk_position"] = message.chunk_position

                            yield FlowOutput(content=content, metadata=chunk_meta)

                    # === Handle ToolMessage (tool execution result) ===
                    elif ToolMessage and isinstance(message, ToolMessage):
                        # Tool has completed execution
                        # ToolMessage arrives from 'tools' node with result
                        tool_name = getattr(message, "name", "unknown")
                        tool_result = getattr(message, "content", "")

                        logger.info(
                            "Tool call completed: %s - yielding status message with result", tool_name
                        )

                        status_output = FlowOutput(
                            content="",
                            metadata={
                                "streaming": True,
                                "chunk": False,
                                "message_type": message_type,
                                "node": node_name,
                                "tool_name": tool_name,
                                "tool_result": tool_result,  # Raw tool output for UI formatting
                                "event_type": "tool_call_complete",
                                "status_message": f"✅ Tool {tool_name} completed",
                            },
                        )
                        logger.info(
                            "Yielding tool_call_complete: content=%r, metadata=%s",
                            status_output.content,
                            status_output.metadata
                        )
                        yield status_output

                elif stream_mode == "updates":
                    # chunk is dict like {'node_name': {'messages': [...]}}
                    for node_name, data in chunk.items():
                        logger.info("Streaming update for node %s: %s", node_name, data)

                        if node_name != "model":
                            continue

                        messages = data.get("messages") if isinstance(data, dict) else None
                        if not messages:
                            continue

                        aggregated_usage = aggregate_token_usage(messages)
                        if aggregated_usage:
                            token_usage = aggregated_usage

                        for message in messages:
                            tool_calls = getattr(message, "tool_calls", None)
                            if not tool_calls:
                                continue

                            for tool_call in tool_calls:
                                if not isinstance(tool_call, Mapping) or "name" not in tool_call:
                                    continue
                                tool_names.append(str(tool_call["name"]))
                                tool_name = tool_call.get("name", "unknown")
                                tool_args = tool_call.get("args", {})

                                # Format tool call with arguments
                                formatted_call = self._format_tool_call(tool_name, tool_args)

                                status_output = FlowOutput(
                                    content="",
                                    metadata={
                                        "streaming": True,
                                        "chunk": False,
                                        "message_type": message_type,
                                        "node": node_name,
                                        "tool_name": tool_name,
                                        "event_type": "tool_call_start",
                                        "status_message": f"🔧 {formatted_call}",
                                    },
                                )
                                logger.info(
                                    "Yielding tool_call_start from updates: content=%r, metadata=%s",
                                    status_output.content,
                                    status_output.metadata,
                                )
                                yield status_output

        except Exception as exc:
            logger.error("LangChain create_agent streaming failed: %s", exc)
            yield FlowOutput(
                content=f"Error: {exc}",
                metadata={
                    "error": True,
                    "streaming": True,
                    "exception_type": type(exc).__name__,
                },
            )
            return

        # Final metadata update indicating stream completion
        yield FlowOutput(
            content="",
            metadata={
                "streaming": True,
                "final": True,
                "model": self.model.model_name,
                "tools_available": len(self.tools),
                **({"token_usage": token_usage} if token_usage else {}),
                **({"tool_calls": list(dict.fromkeys(tool_names))} if tool_names else {}),
            },
        )

    async def cleanup(self) -> None:
        """Close MCP client connections and clean up resources."""

        # MultiServerMCPClient doesn't need manual cleanup
        #for client in self._mcp_clients:
        #    try:
        #        if hasattr(client, "__aexit__"):
        #            await client.__aexit__(None, None, None)
        #            logger.debug("Closed MCP client connection")
        #    except Exception:  # pragma: no cover - best-effort cleanup
        #        logger.debug("Ignoring MCP client close error", exc_info=True)

    def _format_tool_call(self, tool_name: str, tool_input: Any) -> str:
        """Format a tool call as a function signature.

        Args:
            tool_name: Name of the tool being called
            tool_input: Arguments passed to the tool (dict or other)

        Returns:
            Formatted string like: "Calling tool: tool_name(arg1='value1', arg2='value2')"
        """
        if not tool_input:
            return f"Calling tool: {tool_name}()"

        # Handle dict input (most common case)
        if isinstance(tool_input, dict):
            # Format as key=value pairs
            args_parts = []
            for key, value in tool_input.items():
                # Format value with quotes if it's a string
                if isinstance(value, str):
                    formatted_value = f'"{value}"'
                else:
                    formatted_value = str(value)
                args_parts.append(f"{key}={formatted_value}")

            args_str = ", ".join(args_parts)
            return f"Calling tool: {tool_name}({args_str})"

        # Handle non-dict input (rare, but possible)
        return f"Calling tool: {tool_name}({tool_input!r})"

    def _extract_token_usage(self, state: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from the final AIMessage in the state."""

        messages: Sequence["BaseMessage"]
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        return aggregate_token_usage(messages)

    def _extract_tool_calls(self, state: Any) -> List[str]:
        """Collect tool names from AIMessage.tool_calls entries."""

        messages: Sequence["BaseMessage"]
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        return collect_tool_call_names(messages)

    def _build_langgraph_config(self, session_id: str) -> "RunnableConfig":
        """Build LangGraph configuration with thread_id.

        Maps ATHOS session_id to LangGraph thread_id for checkpoint persistence.

        Args:
            session_id: ATHOS session identifier

        Returns:
            RunnableConfig with thread_id and recursion_limit configured
        """
        return {
            "configurable": {
                "thread_id": session_id
            },
            "recursion_limit": self.max_iterations
        }

    def _build_messages(self, input: FlowInput) -> List[BaseMessage]:
        """Build message list containing only the new user message.

        With checkpointing enabled, the LangGraph checkpoint automatically
        loads previous conversation history based on the thread_id.
        We only need to provide the new message.

        Args:
            input: Flow input containing the new user message

        Returns:
            List containing only the new HumanMessage
        """
        return Message.to_langchain_list([input.message])

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

            # Create checkpointer if not exists
            if self._checkpointer is None:
                if InMemorySaver is None:
                    raise ImportError(
                        "The 'langgraph' package is required for checkpointing."
                    ) from _CREATE_AGENT_IMPORT_ERROR
                self._checkpointer = InMemorySaver()
                logger.debug("Initialized InMemorySaver checkpointer")

            system_prompt = self.system_prompt or None
            self._graph = create_agent(
                self.model,
                list(self.tools),
                system_prompt=system_prompt,
                checkpointer=self._checkpointer
            )
            self._graph_needs_rebuild = False

            logger.debug(
                "Built LangChain create_agent graph with %d tools and checkpointing enabled",
                len(self.tools)
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
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt provided to the LangChain agent.",
    )
    system_prompt_path: Optional[str] = Field(
        default=None,
        description="Path to a file containing the system prompt for the agent.",
    )
    @model_validator(mode='before')
    @classmethod
    def load_system_prompt_from_path(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data

        prompt = data.get('system_prompt')
        prompt_path = data.get('system_prompt_path')

        if prompt and prompt_path:
            raise ValueError('Provide either system_prompt or system_prompt_path, not both')

        if prompt_path:
            expanded = expand_env(prompt_path)
            base_dir = Path(info.context['config_dir']) if info.context and 'config_dir' in info.context else Path.cwd()
            resolved = resolve_path(base_dir, expanded or prompt_path)
            data['system_prompt'] = read_text_file(resolved)

        return data

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

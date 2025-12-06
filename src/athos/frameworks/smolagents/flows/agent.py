from typing import Any, ClassVar, List, Optional
from typing_extensions import Literal
from enum import Enum
import asyncio
import logging
from pathlib import Path
from pydantic import Field, model_validator, ValidationInfo

from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    Tool,
    OpenAIServerModel,
    MCPClient,
)

from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode
from athos.models.metrics import ExecutionMetrics, TokenUsage, ToolCallInfo
from athos.registry.flow_registry import register_flow
from athos.config.models import (
    AthosConfig,
    BaseFlowConfig,
    MCPServerConfig,
    ModelConfig,
    ToolConfig,
    ToolFramework,
    expand_env,
)
from athos.utils.paths import resolve_path, read_text_file
from athos.frameworks.smolagents.factories import (
    build_mcp_client,
    build_model,
    build_tool,
)

logger = logging.getLogger(__name__)


class AgentFlow(BaseFlow):
    """General agent flow supporting multiple agent types."""

    # ===== Class metadata (new pattern) =====
    name: ClassVar[str] = "smol_agent"
    description: ClassVar[str] = "SmolAgents tool-calling or code-executing agent"
    framework: ClassVar[ToolFramework] = ToolFramework.SMOLAGENTS
    supported_modes: ClassVar[List[ExecutionMode]] = [ExecutionMode.SYNC]

    def __init__(
        self,
        model: OpenAIServerModel,
        tools: List[Tool],
        agent_type: str,
        mcp_clients: Optional[List[MCPClient]],
        full_config: AthosConfig,
        **agent_kwargs,
    ):
        """
        Construct an agent flow with all dependencies.

        Note: Use the create() classmethod in production.
        This constructor is public to support testing with mocks.

        Args:
            model: SmolAgents model (required)
            tools: List of tools available to the agent
            agent_type: Type of agent ("code" or "tool_calling")
            mcp_clients: Optional list of MCP clients
            full_config: Full ATHOS configuration
            **agent_kwargs: Additional arguments for the agent
        """
        self._full_config = full_config
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

    @classmethod
    async def create(
        cls,
        flow_config: "AgentFlowConfig",
        athos_config: AthosConfig
    ) -> "AgentFlow":
        """
        Create and fully initialize an agent flow.

        Builds the model, tools, and MCP clients and constructs the flow instance.

        Args:
            flow_config: Agent-specific configuration
            athos_config: Full ATHOS configuration

        Returns:
            Fully initialized agent flow
        """
        # Build model
        if flow_config.model not in athos_config.models:
            raise ValueError(
                f"Model '{flow_config.model}' not found in configuration"
            )
        model_cfg = athos_config.models[flow_config.model]
        model = build_model(model_cfg)

        # Build tools
        tool_instances: List[Tool] = []
        for tool_name in flow_config.tools:
            if tool_name not in athos_config.tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in configuration"
                )
            tool_cfg: ToolConfig = athos_config.tools[tool_name]
            tool_instances.append(build_tool(tool_cfg))

        # Build MCP clients
        mcp_instances: List[MCPClient] = []
        combined_instructions: List[str] = []
        if flow_config.instructions:
            combined_instructions.append(flow_config.instructions)

        for mcp_name in flow_config.mcp_servers:
            if mcp_name not in athos_config.mcp_servers:
                raise ValueError(
                    f"MCP server '{mcp_name}' not found in configuration"
                )
            mcp_cfg: MCPServerConfig = athos_config.mcp_servers[mcp_name]
            client = build_mcp_client(mcp_name, mcp_cfg)
            mcp_instances.append(client)
            if mcp_cfg.instructions:
                combined_instructions.append(mcp_cfg.instructions)

        instructions = "\n\n".join(combined_instructions) if combined_instructions else None

        # Construct flow with all dependencies
        return cls(
            model=model,
            tools=tool_instances,
            agent_type=flow_config.agent_type.value,
            mcp_clients=mcp_instances,
            full_config=athos_config,
            max_steps=flow_config.max_steps,
            verbosity_level=flow_config.verbosity_level,
            additional_authorized_imports=flow_config.additional_authorized_imports,
            instructions=instructions,
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """
        Execute the agent flow once and return structured output.

        Args:
            input: FlowInput containing message and session

        Returns:
            FlowOutput with agent response and execution metrics
        """
        message = input.message

        try:
            # Run agent with return_full_result to get detailed metrics
            result = await asyncio.to_thread(
                self.agent.run,
                message,
                reset=False,
                return_full_result=True
            )

            # Build execution metrics
            metrics = ExecutionMetrics(
                model_name=self.agent.model.model_id if hasattr(self.agent.model, 'model_id') else None,
            )

            # Extract token usage if available
            if hasattr(result, 'token_usage') and result.token_usage:
                metrics.token_usage = TokenUsage(
                    input_tokens=result.token_usage.input_tokens,
                    output_tokens=result.token_usage.output_tokens,
                )

            # Extract tool calls from steps
            if hasattr(result, 'steps') and result.steps:
                tool_calls_map = {}
                for step in result.steps:
                    # Check if step has tool_calls attribute or is a dict with tool_calls
                    step_tool_calls = None
                    if isinstance(step, dict):
                        step_tool_calls = step.get('tool_calls', [])
                    elif hasattr(step, 'tool_calls'):
                        step_tool_calls = step.tool_calls

                    if step_tool_calls:
                        for tc in step_tool_calls:
                            # Extract tool name from different formats
                            tool_name = None
                            if isinstance(tc, dict):
                                # OpenAI-style format: {'id': '...', 'function': {'name': '...', 'arguments': '...'}}
                                if 'function' in tc and isinstance(tc['function'], dict):
                                    tool_name = tc['function'].get('name')
                                # Direct format: {'name': '...'}
                                elif 'name' in tc:
                                    tool_name = tc['name']
                            elif hasattr(tc, 'name'):
                                tool_name = tc.name
                            elif hasattr(tc, 'function') and hasattr(tc.function, 'name'):
                                tool_name = tc.function.name

                            if tool_name:
                                if tool_name in tool_calls_map:
                                    tool_calls_map[tool_name].call_count += 1
                                else:
                                    tool_calls_map[tool_name] = ToolCallInfo(name=tool_name, call_count=1)

                metrics.tool_calls = list(tool_calls_map.values())
                metrics.step_count = len(result.steps)

            # Build metadata from metrics
            metadata = {
                "agent_type": self.agent_type,
                "tools_available": len(self.agent.tools) if hasattr(self.agent, 'tools') else 0,
            }
            metadata.update(metrics.to_dict())

            # Extract output content from RunResult
            content = str(result.output) if hasattr(result, 'output') else str(result)

            return FlowOutput(
                content=content,
                metadata=metadata
            )
        except Exception as e:
            logger.error("%s execution failed: %s", self.agent.__class__.__name__, e)
            return FlowOutput(
                content=f"Error: {e}",
                metadata={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Disconnect any MCP clients held by this flow."""
        for client in self._mcp_clients:
            try:
                client.disconnect()
                logger.debug("Disconnected MCP client")
            except Exception as e:  # pragma: no cover - disconnect failures should not crash
                logger.warning("Error disconnecting MCP client: %s", e)
        self._mcp_clients.clear()


class AgentType(str, Enum):
    """Supported agent implementations"""
    CODE = "code"
    TOOL_CALLING = "tool_calling"


class AgentFlowConfig(BaseFlowConfig):
    type: Literal["smol_agent"]
    model: str
    agent_type: AgentType = AgentType.CODE
    mcp_servers: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    max_steps: int = Field(default=10, gt=0)
    verbosity_level: Optional[int] = Field(default=1)
    additional_authorized_imports: List[str] = Field(default_factory=list)
    instructions: Optional[str] = Field(default=None)
    instructions_path: Optional[str] = Field(default=None)

    @model_validator(mode='before')
    @classmethod
    def load_instructions_from_path(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data

        instructions = data.get('instructions')
        instructions_path = data.get('instructions_path')

        if instructions and instructions_path:
            raise ValueError('Provide either instructions or instructions_path, not both')

        if instructions_path:
            expanded = expand_env(instructions_path)
            base_dir = Path(info.context['config_dir']) if info.context and 'config_dir' in info.context else Path.cwd()
            resolved = resolve_path(base_dir, expanded or instructions_path)
            data['instructions'] = read_text_file(resolved)

        return data

# Set config_class on the flow class
AgentFlow.config_class = AgentFlowConfig

# Register using new pattern
register_flow(AgentFlow)


__all__ = ["AgentFlow", "AgentFlowConfig"]

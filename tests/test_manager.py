import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from athos.core.manager import AthosManager, create_athos_manager
from athos.config import (
    AthosConfig,
    ToolConfig,
    MCPServerConfig,
    MCPType,
    ExecutionFlowType,
    ModelConfig,
    ChatbotFlowConfig,
    AgentFlowConfig,
)
from smolagents import Tool
from smolagents.mcp_client import MCPClient


class TestAthosManager:

    @pytest.fixture
    def mock_model_config(self):
        return ModelConfig(
            model_id="test-model",
            api_base="http://test-api",
            api_key="test-key"
        )

    @pytest.fixture
    def mock_tool_config(self):
        return ToolConfig(
            module_path="test.module",
            class_name="TestTool",
            parameters={"param1": "value1"}
        )

    @pytest.fixture
    def mock_mcp_server_config(self):
        return MCPServerConfig(
            mcp_type=MCPType.MCP_STDIO,
            command="test-mcp-command",
            args=["--arg1", "value1"]
        )

    @pytest.fixture
    def mock_flow_config(self):
        return ChatbotFlowConfig(
            type=ExecutionFlowType.CHATBOT,
            model="test_model",
            system_prompt="Test prompt",
        )

    @pytest.fixture
    def mock_config(self, mock_model_config, mock_tool_config, mock_mcp_server_config, mock_flow_config):
        return AthosConfig(
            models={"test_model": mock_model_config},
            tools={"test_tool": mock_tool_config},
            mcp_servers={"test_mcp_server": mock_mcp_server_config},
            execution_flows={"test_flow": mock_flow_config}
        )

    @patch('athos.core.manager.OpenAIServerModel')
    def test_lazy_model_loading(self, mock_openai_model, mock_config):
        """Models should be instantiated only when accessed"""
        manager = AthosManager(mock_config)

        # No model loaded at initialization
        mock_openai_model.assert_not_called()
        assert manager.models == {}

        # Fetching a model should create it
        model = manager._get_or_create_model("test_model")
        mock_openai_model.assert_called_once_with(
            model_id="test-model",
            api_base="http://test-api",
            api_key="test-key"
        )
        assert manager.models["test_model"] is model

    @patch('athos.core.manager.MCPClient')
    @patch('athos.core.manager.StdioServerParameters')
    def test_create_mcp_client_stdio(self, mock_stdio_params, mock_mcp_client, mock_config):
        """Test MCP client creation for stdio"""
        manager = AthosManager(mock_config)

        mcp_config = MCPServerConfig(
            mcp_type=MCPType.MCP_STDIO,
            command="test-command",
            args=["arg1", "arg2"],
            env={"ENV_VAR": "value"}
        )

        client = manager._create_mcp_client("test_mcp", mcp_config)

        mock_stdio_params.assert_called_once_with(
            command="test-command",
            args=["arg1", "arg2"],
            env={"ENV_VAR": "value"}
        )
        mock_mcp_client.assert_called_once()
        assert client is not None

    @patch('athos.core.manager.MCPClient')
    def test_create_mcp_client_sse(self, mock_mcp_client, mock_config):
        """Test MCP client creation for SSE"""
        manager = AthosManager(mock_config)

        mcp_config = MCPServerConfig(
            mcp_type=MCPType.MCP_SSE,
            url="http://test-url",
            headers={"Authorization": "Bearer token"}
        )

        client = manager._create_mcp_client("test_mcp", mcp_config)

        mock_mcp_client.assert_called_once_with({
            "url": "http://test-url",
            "headers": {"Authorization": "Bearer token"}
        })
        assert client is not None


    # Note: MCP tool loading tests removed as MCP functionality
    # has been moved out of the tool building path

    @patch('builtins.__import__')
    def test_load_tool_success(self, mock_import, mock_config):
        """Test successful tool loading"""
        manager = AthosManager(mock_config)

        # Mock the imported module and tool class
        mock_tool_instance = Mock(spec=Tool)
        mock_tool_class = Mock(return_value=mock_tool_instance)
        mock_module = Mock()
        mock_module.TestTool = mock_tool_class
        mock_import.return_value = mock_module

        tool_config = ToolConfig(
            module_path="test.module",
            class_name="TestTool",
            parameters={"param1": "value1"}
        )

        result = manager._load_tool("test_tool", tool_config)

        mock_import.assert_any_call("test.module", fromlist=["TestTool"])
        mock_tool_class.assert_called_once_with(param1="value1")
        assert result == mock_tool_instance
        assert manager.loaded_tools["test_tool"] == mock_tool_instance

    def test_load_tool_cached(self, mock_config):
        """Test tool loading from cache"""
        manager = AthosManager(mock_config)

        cached_tool = Mock(spec=Tool)
        manager.loaded_tools["test_tool"] = cached_tool

        tool_config = ToolConfig(
            class_name="TestTool",
            module_path="test.module"
        )

        result = manager._load_tool("test_tool", tool_config)

        assert result == cached_tool

    @pytest.mark.asyncio
    @patch('athos.core.builtin_flows.ChatbotFlow')
    @patch('athos.core.manager.OpenAIServerModel')
    async def test_lazy_chatbot_flow_creation(self, mock_model, mock_chatbot_flow, mock_config):
        """Flow should be created only when executed"""
        mock_flow_instance = AsyncMock()
        mock_chatbot_flow.return_value = mock_flow_instance

        manager = AthosManager(mock_config)

        # Flow constructor should not be called during initialization
        mock_chatbot_flow.assert_not_called()

        await manager.execute_flow("test_flow", "hi")

        mock_chatbot_flow.assert_called_once()

    @pytest.mark.asyncio
    @patch('athos.core.builtin_flows.AgentFlow')
    @patch('athos.core.manager.AthosManager._load_tool')
    @patch('athos.core.manager.OpenAIServerModel')
    async def test_lazy_code_agent_flow_creation(self, mock_model, mock_load_tool, mock_code_flow):
        """Code agent flow should be created lazily"""
        # Setup config with code agent flow
        flow_config = AgentFlowConfig(
            type=ExecutionFlowType.AGENT,
            model="test_model",
            agent_type="code",
            tools=["test_tool"],
        )

        config = AthosConfig(
            models={"test_model": ModelConfig(model_id="test", api_base="http://test-api", api_key="test")},
            tools={"test_tool": ToolConfig(
                class_name="TestTool",
                module_path="test.module"
            )},
            mcp_servers={},
            execution_flows={"code_flow": flow_config}
        )

        mock_tool = Mock(spec=Tool)
        mock_load_tool.return_value = mock_tool
        mock_flow_instance = AsyncMock()
        mock_code_flow.return_value = mock_flow_instance

        manager = AthosManager(config)

        mock_code_flow.assert_not_called()

        await manager.execute_flow("code_flow", "do it")

        mock_load_tool.assert_called_once()
        mock_code_flow.assert_called_once()
        assert "code_flow" in manager.flows

    @pytest.mark.asyncio
    @patch('athos.core.builtin_flows.ChatbotFlow')
    @patch('athos.core.manager.OpenAIServerModel')
    async def test_flow_instantiated_only_once(self, mock_model, mock_chatbot_flow, mock_config):
        """Ensure flow objects are created a single time"""
        mock_flow_instance = AsyncMock()
        mock_chatbot_flow.return_value = mock_flow_instance

        manager = AthosManager(mock_config)

        await manager.execute_flow("test_flow", "one")
        await manager.execute_flow("test_flow", "two")

        mock_chatbot_flow.assert_called_once()
        assert mock_flow_instance.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_flow_success(self, mock_config):
        """Test successful flow execution"""
        manager = AthosManager(mock_config)

        mock_flow = AsyncMock()
        mock_flow.execute.return_value = "test result"
        manager.flows["test_flow"] = mock_flow

        result = await manager.execute_flow("test_flow", "test input")

        mock_flow.execute.assert_called_once_with("test input")
        assert result == "test result"

    @pytest.mark.asyncio
    async def test_execute_flow_unknown(self, mock_config):
        """Test execution of unknown flow"""
        manager = AthosManager(mock_config)

        with pytest.raises(ValueError, match="Unknown execution flow: unknown_flow"):
            await manager.execute_flow("unknown_flow", "test input")

    def test_list_flows(self, mock_config):
        """Test listing available flows"""
        manager = AthosManager(mock_config)

        flows = manager.list_flows()

        assert "test_flow" in flows
        assert len(flows) == 1

    def test_get_flow_info_success(self, mock_config):
        """Test getting flow information"""
        manager = AthosManager(mock_config)

        info = manager.get_flow_info("test_flow")

        expected_info = {
            "name": "test_flow",
            "type": "chatbot",
            "model": "test_model",
            "tools": [],
            "mcp_servers": [],
            "has_prompt_chain": False
        }

        assert info == expected_info

    def test_get_flow_info_unknown(self, mock_config):
        """Test getting info for unknown flow"""
        manager = AthosManager(mock_config)

        with pytest.raises(ValueError, match="Unknown execution flow: unknown_flow"):
            manager.get_flow_info("unknown_flow")

    def test_close_cleanup(self, mock_config):
        """Test cleanup of resources"""
        manager = AthosManager(mock_config)

        # Add mock MCP client
        mock_client = Mock()
        mock_client.disconnect = Mock()
        manager.mcp_clients["test_client"] = mock_client

        manager.close()

        mock_client.disconnect.assert_called_once()
        assert len(manager.mcp_clients) == 0

    def test_close_cleanup_no_close_method(self, mock_config):
        """Test cleanup when client has no close method"""
        manager = AthosManager(mock_config)

        # Add mock MCP client without close method
        mock_client = Mock(spec=[])  # No close method
        manager.mcp_clients["test_client"] = mock_client

        # Should not raise exception
        manager.close()

        assert len(manager.mcp_clients) == 0


class TestCreateAthosManager:

    @patch('athos.core.manager.ConfigLoader.load_config')
    @patch('athos.core.manager.AthosManager')
    def test_create_athos_manager(self, mock_manager_class, mock_load_config):
        """Test factory function for creating ATHOS manager"""
        mock_config = Mock(spec=AthosConfig)
        mock_load_config.return_value = mock_config
        mock_manager_instance = Mock()
        mock_manager_class.return_value = mock_manager_instance

        result = create_athos_manager("test_config.yaml")

        mock_load_config.assert_called_once_with("test_config.yaml")
        mock_manager_class.assert_called_once_with(mock_config)
        assert result == mock_manager_instance


# Integration test fixtures and helpers
class TestAthosManagerIntegration:
    """Integration tests that test multiple components together"""

    @pytest.fixture
    def full_config(self):
        """Complete configuration for integration testing"""
        return AthosConfig(
            models={
                "gpt4": ModelConfig(
                    model_id="gpt-4",
                    api_base="https://api.openai.com/v1",
                    api_key="test-key"
                )
            },
            tools={
                "calculator": ToolConfig(
                    module_path="test.tools",
                    class_name="Calculator",
                    parameters={}
                )
            },
            mcp_servers={
                "file_manager_server": MCPServerConfig(
                    mcp_type=MCPType.MCP_STDIO,
                    command="file-server",
                    args=["--root", "/tmp"]
                )
            },
            execution_flows={
                "chat": ChatbotFlowConfig(
                    type=ExecutionFlowType.CHATBOT,
                    model="gpt4",
                    system_prompt="You are a helpful assistant",
                ),
                "coding": AgentFlowConfig(
                    type=ExecutionFlowType.AGENT,
                    model="gpt4",
                    agent_type="code",
                    tools=["calculator"],
                    mcp_servers=["file_manager_server"],
                ),
            }
        )

    @patch('athos.core.manager.OpenAIServerModel')
    @patch('builtins.__import__')
    @patch('athos.core.manager.MCPClient')
    def test_full_initialization(self, mock_mcp_client, mock_import, mock_openai_model, full_config):
        """Test complete manager initialization with multiple components"""
        # Mock regular tool
        mock_calculator = Mock(spec=Tool)
        mock_calculator_class = Mock(return_value=mock_calculator)
        mock_module = Mock()
        mock_module.Calculator = mock_calculator_class
        mock_import.return_value = mock_module

        # Mock MCP client for MCP servers
        mock_client_instance = Mock()
        mock_client_instance.get_tools.return_value = []  # Return empty list instead of Mock
        mock_mcp_client.return_value = mock_client_instance

        with patch('athos.core.manager.StdioServerParameters'), \
             patch('athos.core.builtin_flows.ChatbotFlow') as mock_chatbot_flow, \
             patch('athos.core.builtin_flows.AgentFlow') as mock_code_flow:

            manager = AthosManager(full_config)

            # Models should not be loaded yet
            assert manager.models == {}

            # No flows should be created yet
            assert manager.flows == {}

            # Preload all flows
            manager.preload_flows()

            # Model should be loaded during flow creation
            assert len(manager.models) == 1
            assert "gpt4" in manager.models

            # Verify tools loaded after preload
            assert len(manager.loaded_tools) >= 1  # calculator tool

            assert len(manager.flows) == 2
            assert "chat" in manager.flows
            assert "coding" in manager.flows

            mock_chatbot_flow.assert_called_once()
            mock_code_flow.assert_called_once()

    @patch('athos.core.manager.OpenAIServerModel')
    def test_error_handling_during_initialization(self, mock_openai_model):
        """Test error handling during manager initialization"""
        # Config with invalid tool
        config = AthosConfig(
            models={"test": ModelConfig(model_id="test", api_base="http://test-api", api_key="test")},
            tools={"bad_tool": ToolConfig(
                module_path="nonexistent.module",
                class_name="NonexistentClass"
            )},
            mcp_servers={},
            execution_flows={"test_flow": AgentFlowConfig(
                type=ExecutionFlowType.AGENT,
                model="test",
                agent_type="code",
                tools=["bad_tool"],
            )}
        )

        manager = AthosManager(config)
        with pytest.raises(Exception):  # Should fail during tool loading
            manager.preload_flows()

    @pytest.mark.asyncio
    @patch('athos.core.manager.OpenAIServerModel')
    async def test_end_to_end_flow_execution(self, mock_openai_model):
        """Test end-to-end flow execution"""
        config = AthosConfig(
            models={"test": ModelConfig(model_id="test", api_base="http://test-api", api_key="test")},
            tools={},
            mcp_servers={},
            execution_flows={"chat": ChatbotFlowConfig(
                type=ExecutionFlowType.CHATBOT,
                model="test",
                system_prompt="Test prompt",
            )}
        )

        with patch('athos.core.builtin_flows.ChatbotFlow') as mock_chatbot_flow:
            mock_flow_instance = AsyncMock()
            mock_flow_instance.execute.return_value = "Hello, world!"
            mock_chatbot_flow.return_value = mock_flow_instance

            manager = AthosManager(config)
            result = await manager.execute_flow("chat", "Hello")

            assert result == "Hello, world!"
            mock_flow_instance.execute.assert_called_once_with("Hello")


# Performance and edge case tests
class TestAthosManagerEdgeCases:

    def test_empty_config(self):
        """Test manager with minimal/empty configuration"""
        config = AthosConfig(models={}, tools={}, mcp_servers={}, execution_flows={})

        manager = AthosManager(config)

        assert len(manager.models) == 0
        assert len(manager.loaded_tools) == 0
        assert len(manager.flows) == 0
        assert manager.list_flows() == []

    def test_mcp_client_caching(self):
        """Test that MCP clients are properly cached"""
        config = AthosConfig(models={}, tools={}, mcp_servers={}, execution_flows={})
        manager = AthosManager(config)

        mcp_config = MCPServerConfig(
            mcp_type=MCPType.MCP_STDIO,
            command="test-command"
        )

        with patch('athos.core.manager.MCPClient') as mock_mcp_client, \
             patch('athos.core.manager.StdioServerParameters'):

            # First call should create client
            client1 = manager._create_mcp_client("test_mcp", mcp_config)

            # Second call should return cached client
            client2 = manager._create_mcp_client("test_mcp", mcp_config)

            assert client1 is client2
            assert mock_mcp_client.call_count == 1

    def test_tool_caching_behavior(self):
        """Test tool caching behavior"""
        config = AthosConfig(models={}, tools={}, mcp_servers={}, execution_flows={})
        manager = AthosManager(config)

        tool_config = ToolConfig(
            module_path="test.module",
            class_name="TestTool"
        )

        mock_tool = Mock(spec=Tool)
        
        with patch('builtins.__import__') as mock_import:
            mock_tool_class = Mock(return_value=mock_tool)
            mock_module = Mock()
            mock_module.TestTool = mock_tool_class
            mock_import.return_value = mock_module

            # First load
            result1 = manager._load_tool("test_tool", tool_config)
            # Second load should use cache
            result2 = manager._load_tool("test_tool", tool_config)

            assert result1 == mock_tool
            assert result2 == mock_tool
            assert mock_import.call_count == 1  # Only called once due to caching

    @pytest.mark.asyncio
    async def test_concurrent_flow_execution(self):
        """Test concurrent execution of multiple flows"""
        config = AthosConfig(
            models={"test": ModelConfig(model_id="test", api_base="http://test-api", api_key="test")},
            tools={},
            mcp_servers={},
            execution_flows={
                "flow1": ChatbotFlowConfig(
                    type=ExecutionFlowType.CHATBOT,
                    model="test",
                    system_prompt="Test 1",
                ),
                "flow2": ChatbotFlowConfig(
                    type=ExecutionFlowType.CHATBOT,
                    model="test",
                    system_prompt="Test 2",
                ),
            }
        )

        with patch('athos.core.manager.OpenAIServerModel'), \
             patch('athos.core.builtin_flows.ChatbotFlow') as mock_chatbot_flow:

            mock_flow1 = AsyncMock()
            mock_flow1.execute.return_value = "Result 1"
            mock_flow2 = AsyncMock()
            mock_flow2.execute.return_value = "Result 2"

            mock_chatbot_flow.side_effect = [mock_flow1, mock_flow2]

            manager = AthosManager(config)

            # Execute flows concurrently
            results = await asyncio.gather(
                manager.execute_flow("flow1", "Input 1"),
                manager.execute_flow("flow2", "Input 2")
            )

            assert results == ["Result 1", "Result 2"]
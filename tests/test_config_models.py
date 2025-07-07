"""
Comprehensive unit tests for ATHOS configuration models.

This test suite focuses on field validators, model validators, and Pydantic constraints
as specified in the test plan. It provides thorough coverage of all validation logic
in src/athos/config/models.py.
"""

import os
import pytest
from pydantic import ValidationError
from athos.config.models import (
    MCPType,
    ModelConfig,
    MCPServerConfig,
    ToolConfig,
    ChatbotFlowConfig,
    AgentFlowConfig,
    PromptChainFlowConfig,
    AthosConfig,
)


class TestMCPType:
    """Test MCPType enum validation."""
    
    def test_valid_mcp_types(self):
        """Test all valid enum values."""
        assert MCPType.MCP_STDIO == "mcp_stdio"
        assert MCPType.MCP_SSE == "mcp_sse"
    
    def test_string_enum_behavior(self):
        """Test that enum values can be used as strings."""
        mcp_type = MCPType.MCP_STDIO
        assert mcp_type.value == "mcp_stdio"
        assert mcp_type == "mcp_stdio"  # String comparison works
    
    def test_enum_in_model_validation(self):
        """Test enum validation within MCPServerConfig."""
        # Valid enum usage
        config = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="test-command")
        assert config.mcp_type == MCPType.MCP_STDIO
        
        # Test string value also works
        config = MCPServerConfig(mcp_type="mcp_stdio", command="test-command")
        assert config.mcp_type == MCPType.MCP_STDIO


class TestModelConfig:
    """Test ModelConfig validation including field validators, constraints, and post-init processing."""
    
    def test_required_fields(self):
        """Test that model_id is required."""
        # Valid minimal config
        config = ModelConfig(model_id="test-model")
        assert config.model_id == "test-model"
        
        # Missing model_id should fail
        with pytest.raises(ValidationError):
            ModelConfig()
    
    def test_default_values(self):
        """Test default field values."""
        config = ModelConfig(model_id="test-model")
        assert config.api_key is None
        assert config.api_base is None
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
        assert config.system_prompt is None
    
    # Field Validator Tests
    def test_valid_api_base_urls(self):
        """Test valid HTTP/HTTPS URLs for api_base."""
        valid_urls = [
            "http://localhost:8000",
            "https://api.openai.com/v1",
            "http://127.0.0.1:3000",
            "https://custom-api.example.com/v2",
            "http://api.local:8080/v1",
            "https://secure-api.company.com"
        ]
        for url in valid_urls:
            config = ModelConfig(model_id="test", api_base=url)
            assert config.api_base == url
    
    def test_invalid_api_base_urls(self):
        """Test invalid URL formats for api_base."""
        invalid_urls = [
            "localhost:8000",  # Missing protocol
            "ftp://example.com",  # Wrong protocol
            "not-a-url",  # Not a URL
            "file:///path/to/file",  # Wrong protocol
            "ws://websocket.com",  # Wrong protocol
            "tcp://server:8080"  # Wrong protocol
        ]
        for url in invalid_urls:
            with pytest.raises(ValidationError, match="api_base must be a valid HTTP/HTTPS URL"):
                ModelConfig(model_id="test", api_base=url)
    
    def test_none_api_base(self):
        """Test that None api_base is allowed."""
        config = ModelConfig(model_id="test", api_base=None)
        assert config.api_base is None
    
    def test_empty_string_api_base(self):
        """Test that empty string api_base is processed in post_init."""
        config = ModelConfig(model_id="test", api_base="")
        # Empty string gets processed by os.path.expandvars and becomes None in post_init
        assert config.api_base is None
    
    # Constraint Tests
    def test_temperature_constraints(self):
        """Test temperature range validation (0.0-2.0)."""
        # Test valid temperature values
        valid_temps = [0.0, 0.1, 0.5, 1.0, 1.5, 1.9, 2.0]
        for temp in valid_temps:
            config = ModelConfig(model_id="test", temperature=temp)
            assert config.temperature == temp
        
        # Test invalid temperature values
        invalid_temps = [-0.1, -1.0, 2.1, 3.0, 10.0, -10.0]
        for temp in invalid_temps:
            with pytest.raises(ValidationError):
                ModelConfig(model_id="test", temperature=temp)
    
    def test_max_tokens_constraints(self):
        """Test max_tokens positive validation (>0)."""
        # Test valid max_tokens values
        valid_tokens = [1, 10, 100, 1000, 4096, 8192, 16384]
        for tokens in valid_tokens:
            config = ModelConfig(model_id="test", max_tokens=tokens)
            assert config.max_tokens == tokens
        
        # Test invalid max_tokens values
        invalid_tokens = [0, -1, -10, -100]
        for tokens in invalid_tokens:
            with pytest.raises(ValidationError):
                ModelConfig(model_id="test", max_tokens=tokens)
    
    # Environment Variable Tests
    def test_environment_variable_expansion_api_key(self, monkeypatch):
        """Test api_key environment variable expansion."""
        monkeypatch.setenv('TEST_API_KEY', 'secret123')
        config = ModelConfig(model_id="test", api_key="${TEST_API_KEY}")
        assert config.api_key.get_secret_value() == "secret123"
    
    def test_environment_variable_expansion_api_base(self, monkeypatch):
        """Test api_base environment variable expansion."""
        monkeypatch.setenv('TEST_API_BASE', 'https://api.test.com')
        # Need to bypass field validation by using a valid URL first, then test expansion
        # The field validator runs before post_init, so we need a different approach
        config = ModelConfig(model_id="test", api_base="${TEST_API_BASE}")
        # Manually set and expand to test the post_init logic
        #config.api_base = "${TEST_API_BASE}"
        #config.model_post_init(None)
        assert config.api_base == "https://api.test.com"
    
    def test_missing_environment_variables(self, monkeypatch):
        """Test behavior with missing environment variables."""
        monkeypatch.delenv('MISSING_VAR', raising=False)
        config = ModelConfig(model_id="test", api_key="${MISSING_VAR}")
        assert config.api_key.get_secret_value() == "${MISSING_VAR}"  # Should remain unexpanded
    
    def test_complex_environment_variable_expansion(self, monkeypatch):
        """Test complex environment variable scenarios."""
        monkeypatch.setenv('API_HOST', 'api.example.com')
        monkeypatch.setenv('API_VERSION', 'v1')
        config = ModelConfig(
            model_id="test", 
            api_base="https://${API_HOST}/${API_VERSION}"
        )
        assert config.api_base == "https://api.example.com/v1"
    
    def test_none_values_not_expanded(self):
        """Test that None values are not processed for expansion."""
        config = ModelConfig(model_id="test", api_key=None, api_base=None)
        assert config.api_key is None
        assert config.api_base is None
    
    # Extra Fields Tests
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ModelConfig(model_id="test", extra_field="not_allowed")
    
    def test_multiple_extra_fields_forbidden(self):
        """Test that multiple extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ModelConfig(
                model_id="test", 
                extra_field1="not_allowed",
                extra_field2="also_not_allowed"
            )


class TestMCPServerConfig:
    """Test MCPServerConfig validation including model validators and field validators."""
    
    def test_required_fields(self):
        """Test that mcp_type is required."""
        # Missing mcp_type should fail
        with pytest.raises(ValidationError):
            MCPServerConfig()
    
    def test_default_values(self):
        """Test default field values."""
        config = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="test")
        assert config.command == "test"
        assert config.args == []
        assert config.env == {}
        assert config.url is None
        assert config.headers == {}
    
    # Model Validator Tests
    def test_stdio_requires_command(self):
        """Test that STDIO type requires command."""
        # Valid STDIO configuration
        config = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="python server.py")
        assert config.mcp_type == MCPType.MCP_STDIO
        assert config.command == "python server.py"
        
        # STDIO without command should fail
        with pytest.raises(ValidationError, match="MCP stdio server"):
            MCPServerConfig(mcp_type=MCPType.MCP_STDIO)
    
    def test_stdio_with_args_and_env(self):
        """Test STDIO configuration with args and environment variables."""
        config = MCPServerConfig(
            mcp_type=MCPType.MCP_STDIO,
            command="python server.py",
            args=["--port", "8080", "--debug"],
            env={"DEBUG": "1", "PORT": "8080"}
        )
        assert config.args == ["--port", "8080", "--debug"]
        assert config.env == {"DEBUG": "1", "PORT": "8080"}
    
    def test_sse_requires_url(self):
        """Test that SSE type requires URL."""
        # Valid SSE configuration
        config = MCPServerConfig(mcp_type=MCPType.MCP_SSE, url="https://mcp.example.com")
        assert config.mcp_type == MCPType.MCP_SSE
        assert config.url == "https://mcp.example.com"
        
        # SSE without URL should fail
        with pytest.raises(ValidationError, match="MCP SSE server"):
            MCPServerConfig(mcp_type=MCPType.MCP_SSE)
    
    def test_sse_with_headers(self):
        """Test SSE configuration with headers."""
        config = MCPServerConfig(
            mcp_type=MCPType.MCP_SSE,
            url="https://mcp.example.com",
            headers={"Authorization": "Bearer token123", "Content-Type": "application/json"}
        )
        assert config.headers == {"Authorization": "Bearer token123", "Content-Type": "application/json"}
    
    # Field Validator Tests
    def test_valid_sse_urls(self):
        """Test valid URLs for SSE servers."""
        valid_urls = [
            "http://localhost:8080",
            "https://mcp-server.example.com",
            "https://api.mcp.com/v1",
            "http://127.0.0.1:3000",
            "https://secure.mcp-service.org/api"
        ]
        for url in valid_urls:
            config = MCPServerConfig(mcp_type=MCPType.MCP_SSE, url=url)
            assert config.url == url
    
    def test_invalid_sse_urls(self):
        """Test invalid URLs for SSE servers."""
        invalid_urls = [
            "localhost:8080",  # Missing protocol
            "ftp://example.com",  # Wrong protocol
            "not-a-url",  # Not a URL
            "ws://websocket.com",  # Wrong protocol
            "file:///path/to/file"  # Wrong protocol
        ]
        for url in invalid_urls:
            with pytest.raises(ValidationError, match="url must be a valid HTTP/HTTPS URL"):
                MCPServerConfig(mcp_type=MCPType.MCP_SSE, url=url)
    
    def test_none_url_allowed(self):
        """Test that None URL is allowed (for STDIO servers)."""
        config = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="test", url=None)
        assert config.url is None
    
    # Default Factory Tests
    def test_default_factory_fields(self):
        """Test that default factory fields create separate instances."""
        config1 = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="test1")
        config2 = MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="test2")
        
        # Modify one instance
        config1.args.append("arg1")
        config1.env["VAR1"] = "value1"
        config1.headers["Header1"] = "value1"
        
        # Other instance should not be affected
        assert config2.args == []
        assert config2.env == {}
        assert config2.headers == {}
    
    # Extra Fields Tests
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            MCPServerConfig(
                mcp_type=MCPType.MCP_STDIO,
                command="test",
                extra_field="not_allowed"
            )


class TestToolConfig:
    """Test ToolConfig validation."""
    
    def test_required_fields(self):
        """Test required field validation."""
        # Valid configuration
        config = ToolConfig(class_name="TestTool", module_path="test.module")
        assert config.class_name == "TestTool"
        assert config.module_path == "test.module"
        assert config.parameters == {}
        
        # Missing class_name should fail
        with pytest.raises(ValidationError):
            ToolConfig(module_path="test.module")
        
        # Missing module_path should fail
        with pytest.raises(ValidationError):
            ToolConfig(class_name="TestTool")
        
        # Missing both should fail
        with pytest.raises(ValidationError):
            ToolConfig()
    
    def test_parameters_flexibility(self):
        """Test that parameters can handle various data types."""
        params = {
            "string_param": "value",
            "int_param": 42,
            "float_param": 3.14,
            "bool_param": True,
            "list_param": [1, 2, 3],
            "dict_param": {"nested": "value"},
            "none_param": None
        }
        config = ToolConfig(
            class_name="TestTool",
            module_path="test.module",
            parameters=params
        )
        assert config.parameters == params
    
    def test_empty_parameters(self):
        """Test that empty parameters dictionary is default."""
        config = ToolConfig(class_name="TestTool", module_path="test.module")
        assert config.parameters == {}
    
    def test_complex_module_paths(self):
        """Test various module path formats."""
        valid_paths = [
            "module",
            "package.module",
            "deep.package.structure.module",
            "my_package.my_module",
            "package123.module456"
        ]
        for path in valid_paths:
            config = ToolConfig(class_name="TestTool", module_path=path)
            assert config.module_path == path
    
    def test_complex_class_names(self):
        """Test various class name formats."""
        valid_names = [
            "Tool",
            "MyTool",
            "AdvancedCalculatorTool",
            "Tool123",
            "HTTPClient",
            "XMLParser"
        ]
        for name in valid_names:
            config = ToolConfig(class_name=name, module_path="test.module")
            assert config.class_name == name
    
    # Extra Fields Tests
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ToolConfig(
                class_name="TestTool",
                module_path="test.module",
                extra_field="not_allowed"
            )


class TestExecutionFlowConfig:
    """Test ExecutionFlowConfig validation."""
    
    def test_required_fields(self):
        """Test required field validation."""
        # Valid minimal configuration
        config = ChatbotFlowConfig(type="chatbot", model="test_model")
        assert config.type == "chatbot"
        assert config.model == "test_model"
        
        # Missing type should fail
        with pytest.raises(ValidationError):
            ChatbotFlowConfig(model="test_model")
        
        # Missing model should fail
        with pytest.raises(ValidationError):
            ChatbotFlowConfig(type="chatbot")
    
    def test_default_values(self):
        """Test default field values."""
        config = ChatbotFlowConfig(type="chatbot", model="test_model")
        assert config.system_prompt is None
        assert config.max_iterations == 10
    
    def test_valid_flow_types(self):
        """Test all valid flow types."""
        flow_types = [
            ("chatbot", ChatbotFlowConfig),
            ("agent", AgentFlowConfig),
            ("prompt_chain", PromptChainFlowConfig),
        ]
        for flow_type, cfg_cls in flow_types:
            config = cfg_cls(type=flow_type, model="test_model")
            assert config.type == flow_type
    
    def test_max_iterations_constraint(self):
        """Test max_iterations positive validation (>0)."""
        # Test valid max_iterations values
        valid_iterations = [1, 5, 10, 50, 100, 1000]
        for iterations in valid_iterations:
            config = ChatbotFlowConfig(
                type="chatbot",
                model="test_model",
                max_iterations=iterations
            )
            assert config.max_iterations == iterations
        
        # Test invalid max_iterations values
        invalid_iterations = [0, -1, -10, -100]
        for iterations in invalid_iterations:
            with pytest.raises(ValidationError):
                ChatbotFlowConfig(
                    type="chatbot",
                    model="test_model",
                    max_iterations=iterations
                )
    
    def test_optional_fields(self):
        """Test optional field handling."""
        config = AgentFlowConfig(
            type="agent",
            model="test_model",
            agent_type="code",
            mcp_servers=["server1", "server2"],
            tools=["tool1", "tool2"],
        )
        assert config.mcp_servers == ["server1", "server2"]
        assert config.tools == ["tool1", "tool2"]
    
    def test_empty_lists_default(self):
        """Test that empty lists are properly initialized."""
        config1 = AgentFlowConfig(type="agent", model="model1")
        config2 = AgentFlowConfig(type="agent", model="model2")
        
        # Modify one instance
        config1.mcp_servers.append("server1")
        config1.tools.append("tool1")
        
        # Other instance should not be affected
        assert config2.mcp_servers == []
        assert config2.tools == []
    
    def test_prompt_chain_structure(self):
        """Test prompt chain with various structures."""
        prompt_chains = [
            [{"role": "user", "content": "Hello"}],
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            []  # Empty chain
        ]
        for chain in prompt_chains:
            config = PromptChainFlowConfig(
                type="prompt_chain",
                model="test_model",
                prompt_chain=chain,
            )
            assert config.prompt_chain == chain
    
    # Extra Fields Tests
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ChatbotFlowConfig(
                type="chatbot",
                model="test_model",
                extra_field="not_allowed"
            )


class TestAthosConfig:
    """Test AthosConfig integration and reference validation."""
    
    def test_empty_configuration(self):
        """Test minimal/empty configuration."""
        config = AthosConfig()
        assert config.models == {}
        assert config.tools == {}
        assert config.mcp_servers == {}
        assert config.execution_flows == {}
        assert config.hpc_cluster_config is None
        assert config.logging_config is None
    
    def test_default_factory_fields(self):
        """Test that default factory fields create separate instances."""
        config1 = AthosConfig()
        config2 = AthosConfig()
        
        # Modify one instance
        config1.models["test"] = ModelConfig(model_id="test")
        
        # Other instance should not be affected
        assert config2.models == {}
    
    # Reference Validation Tests
    def test_valid_model_references(self):
        """Test valid model references in flows."""
        config = AthosConfig(
            models={"gpt4": ModelConfig(model_id="gpt-4")},
            execution_flows={
                "chat": {
                    "type": "chatbot",
                    "model": "gpt4"
                }
            }
        )
        assert "gpt4" in config.models
        assert config.execution_flows["chat"].model == "gpt4"
    
    def test_invalid_model_references(self):
        """Test invalid model references."""
        with pytest.raises(ValidationError, match="Flow 'chat' references unknown model 'unknown_model'"):
            AthosConfig(
                models={"gpt4": ModelConfig(model_id="gpt-4")},
                execution_flows={
                    "chat": {
                        "type": "chatbot",
                        "model": "unknown_model"
                    }
                }
            )
    
    def test_valid_tool_references(self):
        """Test valid tool references in flows."""
        config = AthosConfig(
            models={"gpt4": ModelConfig(model_id="gpt-4")},
            tools={"calculator": ToolConfig(class_name="Calculator", module_path="tools.calc")},
            execution_flows={
                "code": {
                    "type": "agent",
                    "model": "gpt4",
                    "agent_type": "code",
                    "tools": ["calculator"]
                }
            }
        )
        assert "calculator" in config.tools
        assert "calculator" in config.execution_flows["code"].tools
    
    def test_invalid_tool_references(self):
        """Test invalid tool references."""
        with pytest.raises(ValidationError, match="Flow 'code' references unknown tool 'unknown_tool'"):
            AthosConfig(
                models={"gpt4": ModelConfig(model_id="gpt-4")},
                tools={"calculator": ToolConfig(class_name="Calculator", module_path="tools.calc")},
                execution_flows={
                    "code": {
                        "type": "agent",
                        "model": "gpt4",
                        "agent_type": "code",
                        "tools": ["unknown_tool"]
                    }
                }
            )
    
    def test_valid_mcp_server_references(self):
        """Test valid MCP server references in flows."""
        config = AthosConfig(
            models={"gpt4": ModelConfig(model_id="gpt-4")},
            mcp_servers={"file_server": MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="file-server")},
            execution_flows={
                "agent": {
                    "type": "agent",
                    "model": "gpt4",
                    "agent_type": "tool_calling",
                    "mcp_servers": ["file_server"]
                }
            }
        )
        assert "file_server" in config.mcp_servers
        assert "file_server" in config.execution_flows["agent"].mcp_servers
    
    def test_invalid_mcp_server_references(self):
        """Test invalid MCP server references."""
        with pytest.raises(ValidationError, match="Flow 'agent' references unknown MCP server 'unknown_server'"):
            AthosConfig(
                models={"gpt4": ModelConfig(model_id="gpt-4")},
                mcp_servers={"file_server": MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="file-server")},
                execution_flows={
                    "agent": {
                        "type": "agent",
                        "model": "gpt4",
                        "agent_type": "tool_calling",
                        "mcp_servers": ["unknown_server"]
                    }
                }
            )
    
    def test_multiple_flows_same_references(self):
        """Test multiple flows referencing same resources."""
        config = AthosConfig(
            models={"gpt4": ModelConfig(model_id="gpt-4")},
            tools={"calculator": ToolConfig(class_name="Calculator", module_path="tools.calc")},
            execution_flows={
                "flow1": {
                    "type": "agent",
                    "model": "gpt4",
                    "agent_type": "code",
                    "tools": ["calculator"]
                },
                "flow2": {
                    "type": "agent",
                    "model": "gpt4",
                    "agent_type": "tool_calling",
                    "tools": ["calculator"]
                }
            }
        )
        assert len(config.execution_flows) == 2
        assert config.execution_flows["flow1"].model == "gpt4"
        assert config.execution_flows["flow2"].model == "gpt4"
        assert "calculator" in config.execution_flows["flow1"].tools
        assert "calculator" in config.execution_flows["flow2"].tools
    
    def test_complex_reference_scenario(self):
        """Test complex scenario with multiple references."""
        config = AthosConfig(
            models={
                "gpt4": ModelConfig(model_id="gpt-4"),
                "claude": ModelConfig(model_id="claude-3")
            },
            tools={
                "calculator": ToolConfig(class_name="Calculator", module_path="tools.calc"),
                "web_search": ToolConfig(class_name="WebSearch", module_path="tools.web")
            },
            mcp_servers={
                "file_server": MCPServerConfig(mcp_type=MCPType.MCP_STDIO, command="file-server"),
                "db_server": MCPServerConfig(mcp_type=MCPType.MCP_SSE, url="https://db.example.com")
            },
            execution_flows={
                "chat": {
                    "type": "chatbot",
                    "model": "gpt4"
                },
                "research": {
                    "type": "agent",
                    "model": "claude",
                    "agent_type": "tool_calling",
                    "tools": ["calculator", "web_search"],
                    "mcp_servers": ["file_server", "db_server"]
                }
            }
        )
        # Should validate successfully
        assert len(config.models) == 2
        assert len(config.tools) == 2
        assert len(config.mcp_servers) == 2
        assert len(config.execution_flows) == 2
    
    def test_multiple_invalid_references(self):
        """Test multiple invalid references in single flow."""
        with pytest.raises(ValidationError) as exc_info:
            AthosConfig(
                models={"gpt4": ModelConfig(model_id="gpt-4")},
                tools={"calculator": ToolConfig(class_name="Calculator", module_path="tools.calc")},
                execution_flows={
                    "flow": {
                        "type": "agent",
                        "model": "unknown_model",  # Invalid model
                        "agent_type": "tool_calling",
                        "tools": ["unknown_tool"],  # Invalid tool
                        "mcp_servers": ["unknown_server"]  # Invalid MCP server
                    }
                }
            )
        # Should fail on first invalid reference (model)
        assert "unknown model" in str(exc_info.value)
    
    def test_optional_config_sections(self):
        """Test optional configuration sections."""
        config = AthosConfig(
            models={"gpt4": ModelConfig(model_id="gpt-4")},
            hpc_cluster_config={"cluster_name": "nersc", "partition": "gpu"},
            logging_config={"level": "INFO", "format": "%(message)s"}
        )
        assert config.hpc_cluster_config == {"cluster_name": "nersc", "partition": "gpu"}
        assert config.logging_config == {"level": "INFO", "format": "%(message)s"}
    
    # Extra Fields Tests
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            AthosConfig(extra_field="not_allowed")


class TestErrorHandling:
    """Test error handling and edge cases across all models."""
    
    def test_validation_error_messages(self):
        """Test specific error messages for better debugging."""
        # Temperature constraint error
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(model_id="test", temperature=3.0)
        assert "Input should be less than or equal to 2" in str(exc_info.value)
        
        # API base URL error
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(model_id="test", api_base="invalid-url")
        assert "api_base must be a valid HTTP/HTTPS URL" in str(exc_info.value)
        
        # Max tokens constraint error
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(model_id="test", max_tokens=0)
        assert "Input should be greater than 0" in str(exc_info.value)
    
    def test_nested_validation_errors(self):
        """Test error propagation through nested models."""
        with pytest.raises(ValidationError):
            AthosConfig(
                models={"invalid": ModelConfig(model_id="test", temperature=5.0)},  # Invalid temperature
                execution_flows={
                    "flow": ChatbotFlowConfig(
                        type="chatbot",
                        model="invalid"
                    )
                }
            )
    
    def test_boundary_conditions(self):
        """Test exact boundary values."""
        # Test exact boundary values that should pass
        config = ModelConfig(model_id="test", temperature=0.0, max_tokens=1)
        assert config.temperature == 0.0
        assert config.max_tokens == 1
        
        config = ModelConfig(model_id="test", temperature=2.0)
        assert config.temperature == 2.0
        
        config = ChatbotFlowConfig(
            type="chatbot",
            model="test",
            max_iterations=1,
        )
        assert config.max_iterations == 1
    
    def test_type_coercion(self):
        """Test type coercion behavior."""
        # Test that string numbers are coerced to proper types
        config = ModelConfig(model_id="test", temperature="1.5", max_tokens="2048")
        assert config.temperature == 1.5
        assert config.max_tokens == 2048
        assert isinstance(config.temperature, float)
        assert isinstance(config.max_tokens, int)
    
    def test_enum_case_sensitivity(self):
        """Test flow type case sensitivity."""
        # Valid lowercase flow type should work
        config = ChatbotFlowConfig(type="chatbot", model="test")
        assert config.type == "chatbot"
        
        # Invalid case should fail
        with pytest.raises(ValidationError):
            ChatbotFlowConfig(type="CHATBOT", model="test")
        
        with pytest.raises(ValidationError):
            ChatbotFlowConfig(type="Chatbot", model="test")


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_complete_configuration(self):
        """Test a complete, realistic configuration."""
        config = AthosConfig(
            models={
                "gpt4": ModelConfig(
                    model_id="gpt-4",
                    api_base="https://api.openai.com/v1",
                    temperature=0.7,
                    max_tokens=2048,
                    system_prompt="You are a helpful AI assistant."
                ),
                "local_llm": ModelConfig(
                    model_id="llama2-7b",
                    api_base="http://localhost:8000",
                    temperature=0.5,
                    max_tokens=1024
                )
            },
            tools={
                "calculator": ToolConfig(
                    class_name="Calculator",
                    module_path="athos.tools.calculator",
                    parameters={"precision": 10}
                ),
                "web_search": ToolConfig(
                    class_name="WebSearchTool",
                    module_path="athos.tools.web",
                    parameters={"max_results": 5, "timeout": 30}
                )
            },
            mcp_servers={
                "filesystem": MCPServerConfig(
                    mcp_type=MCPType.MCP_STDIO,
                    command="python",
                    args=["-m", "mcp_filesystem"],
                    env={"ROOT_PATH": "/workspace"}
                ),
                "database": MCPServerConfig(
                    mcp_type=MCPType.MCP_SSE,
                    url="https://db-mcp.example.com/api",
                    headers={"Authorization": "Bearer token123"}
                )
            },
            execution_flows={
                "chatbot": {
                    "type": "chatbot",
                    "model": "gpt4",
                    "system_prompt": "You are a friendly chatbot."
                },
                "code_assistant": {
                    "type": "agent",
                    "model": "local_llm",
                    "agent_type": "code",
                    "tools": ["calculator"],
                    "mcp_servers": ["filesystem"],
                    "max_steps": 20
                },
                "research_agent": {
                    "type": "agent",
                    "model": "gpt4",
                    "agent_type": "tool_calling",
                    "tools": ["calculator", "web_search"],
                    "mcp_servers": ["filesystem", "database"],
                    "max_steps": 15
                }
            },
            hpc_cluster_config={
                "cluster_name": "perlmutter",
                "partition": "gpu",
                "account": "m1234"
            },
            logging_config={
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        )
        
        # Validate the complete configuration
        assert len(config.models) == 2
        assert len(config.tools) == 2
        assert len(config.mcp_servers) == 2
        assert len(config.execution_flows) == 3
        assert config.hpc_cluster_config is not None
        assert config.logging_config is not None
    
    def test_environment_variable_integration(self, monkeypatch):
        """Test environment variables in a complete configuration."""
        # Set up environment variables
        monkeypatch.setenv('OPENAI_API_KEY', 'sk-test123')
        monkeypatch.setenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        monkeypatch.setenv('LOCAL_API_BASE', 'http://localhost:8000')
        
        # Create models with valid URLs first, then test expansion manually
        # since field validation happens before post_init
        gpt4_model = ModelConfig(
            model_id="gpt-4",
            api_base="${OPENAI_API_BASE}",
            api_key="${OPENAI_API_KEY}"
        )
        # Manually set environment variable and test expansion
        #gpt4_model.api_key = "${OPENAI_API_KEY}"
        #gpt4_model.model_post_init(None)
        
        local_model = ModelConfig(
            model_id="local-model",
            api_base="${LOCAL_API_BASE}"
        )

        config = AthosConfig(
            models={
                "gpt4": gpt4_model,
                "local": local_model
            },
            execution_flows={
                "chat": {
                    "type": "chatbot",
                    "model": "gpt4"
                }
            }
        )
        
        # Verify environment variable expansion
        assert config.models["gpt4"].api_key.get_secret_value() == "sk-test123"
        assert config.models["gpt4"].api_base == "https://api.openai.com/v1"
        assert config.models["local"].api_base == "http://localhost:8000"

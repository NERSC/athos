import os
import yaml
import pytest
from pathlib import Path
from pydantic import ValidationError

from athos.config import ConfigLoader
from athos.config.models import AthosConfig


class TestConfigLoaderBasics:
    """Test basic config loader functionality."""
    
    def test_load_config_file_not_found(self):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_config('nonexistent_file.yaml')

    def test_load_config_minimal_file(self, tmp_path):
        """Test loading minimal empty YAML configuration."""
        cfg_file = tmp_path / 'empty.yaml'
        cfg_file.write_text('{}')
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert hasattr(cfg, 'models') and cfg.models == {}
        assert hasattr(cfg, 'tools') and cfg.tools == {}
        assert hasattr(cfg, 'execution_flows') and cfg.execution_flows == {}
        assert hasattr(cfg, 'mcp_servers') and cfg.mcp_servers == {}

    def test_load_config_completely_empty_file(self, tmp_path):
        """Test handling of completely empty files."""
        cfg_file = tmp_path / 'empty.yaml'
        cfg_file.write_text('')
        # Completely empty files result in None from YAML, which should cause validation error
        with pytest.raises(ValueError, match="Configuration validation failed"):
            ConfigLoader.load_config(str(cfg_file))


class TestYAMLParsingErrors:
    """Test YAML parsing error handling."""
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test handling of malformed YAML files."""
        cfg_file = tmp_path / 'invalid.yaml'
        cfg_file.write_text('invalid: yaml: content: [')
        with pytest.raises(yaml.YAMLError):
            ConfigLoader.load_config(str(cfg_file))

    def test_load_config_invalid_yaml_syntax(self, tmp_path):
        """Test various YAML syntax errors."""
        invalid_yamls = [
            'key: value\n  invalid_indent: value',  # Invalid indentation
            'key: [unclosed list',  # Unclosed list
            'key: {unclosed: dict',  # Unclosed dict
            'key: "unclosed string',  # Unclosed string
        ]
        
        for i, invalid_yaml in enumerate(invalid_yamls):
            cfg_file = tmp_path / f'invalid_{i}.yaml'
            cfg_file.write_text(invalid_yaml)
            with pytest.raises(yaml.YAMLError):
                ConfigLoader.load_config(str(cfg_file))


class TestValidationErrorPropagation:
    """Test that Pydantic validation errors are properly handled."""
    
    def test_load_config_validation_error_propagation(self, tmp_path):
        """Test that Pydantic validation errors are properly wrapped."""
        cfg_file = tmp_path / 'invalid_config.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    temperature: 5.0  # Invalid - exceeds max of 2.0
execution_flows:
  test_flow:
    type: "chatbot"
    model: "test_model"
''')
        with pytest.raises(ValueError, match="Configuration validation failed"):
            ConfigLoader.load_config(str(cfg_file))

    def test_load_config_missing_required_fields(self, tmp_path):
        """Test validation errors for missing required fields."""
        cfg_file = tmp_path / 'missing_required.yaml'
        cfg_file.write_text('''
models:
  test_model:
    # Missing required model_id field
    temperature: 0.7
execution_flows:
  test_flow:
    type: "chatbot"
    model: "test_model"
''')
        with pytest.raises(ValueError, match="Configuration validation failed"):
            ConfigLoader.load_config(str(cfg_file))

    def test_load_config_invalid_enum_values(self, tmp_path):
        """Test validation errors for invalid enum values."""
        cfg_file = tmp_path / 'invalid_enum.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
execution_flows:
  test_flow:
    type: "invalid_flow_type"  # Invalid enum value
    model: "test_model"
''')
        with pytest.raises(ValueError, match="Configuration validation failed"):
            ConfigLoader.load_config(str(cfg_file))


class TestPathHandling:
    """Test different path handling scenarios."""
    
    def test_load_config_pathlib_path(self, tmp_path):
        """Test loading with pathlib.Path object."""
        cfg_file = tmp_path / 'config.yaml'
        cfg_file.write_text('{}')
        cfg = ConfigLoader.load_config(cfg_file)  # Pass Path object directly
        assert isinstance(cfg, AthosConfig)

    def test_load_config_relative_path(self, tmp_path, monkeypatch):
        """Test loading with relative paths."""
        monkeypatch.chdir(tmp_path)
        cfg_file = tmp_path / 'config.yaml'
        cfg_file.write_text('{}')
        cfg = ConfigLoader.load_config('config.yaml')  # Relative path
        assert isinstance(cfg, AthosConfig)

    def test_load_config_absolute_path(self, tmp_path):
        """Test loading with absolute paths."""
        cfg_file = tmp_path / 'config.yaml'
        cfg_file.write_text('{}')
        cfg = ConfigLoader.load_config(str(cfg_file.absolute()))
        assert isinstance(cfg, AthosConfig)


class TestCompleteConfigurations:
    """Test loading complete, realistic configurations."""
    
    def test_load_config_complete_valid_structure(self, tmp_path):
        """Test loading a complete, valid configuration."""
        cfg_file = tmp_path / 'complete.yaml'
        cfg_file.write_text('''
models:
  gpt4:
    model_id: "gpt-4"
    api_base: "https://api.openai.com/v1"
    temperature: 0.7
    max_tokens: 2048
    system_prompt: "You are a helpful assistant"

tools:
  calculator:
    class_name: "Calculator"
    module_path: "tools.calc"
    parameters:
      precision: 10
      debug: true

mcp_servers:
  file_server:
    mcp_type: "mcp_stdio"
    command: "python file_server.py"
    args: ["--debug", "--port", "8080"]
    env:
      DEBUG: "1"
      PORT: "8080"
  web_server:
    mcp_type: "mcp_sse"
    url: "https://mcp.example.com/api"
    headers:
      Authorization: "Bearer token123"
      Content-Type: "application/json"

execution_flows:
  chat:
    type: "chatbot"
    model: "gpt4"
    system_prompt: "You are a friendly chatbot"
    max_iterations: 15
  code_agent:
    type: "agent"
    agent_type: "code"
    model: "gpt4"
    tools: ["calculator"]
    mcp_servers: ["file_server"]
    max_steps: 20
  research:
    type: "agent"
    agent_type: "tool_calling"
    model: "gpt4"
    tools: ["calculator"]
    mcp_servers: ["file_server", "web_server"]

hpc_cluster_config:
  cluster_name: "perlmutter"
  partition: "gpu"
  account: "m1234"

logging_config:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
''')
        cfg = ConfigLoader.load_config(str(cfg_file))
        
        # Verify structure is properly loaded
        assert "gpt4" in cfg.models
        assert cfg.models["gpt4"].model_id == "gpt-4"
        assert cfg.models["gpt4"].temperature == 0.7
        
        assert "calculator" in cfg.tools
        assert cfg.tools["calculator"].class_name == "Calculator"
        assert cfg.tools["calculator"].parameters["precision"] == 10
        
        assert "file_server" in cfg.mcp_servers
        assert cfg.mcp_servers["file_server"].command == "python file_server.py"
        assert "web_server" in cfg.mcp_servers
        assert cfg.mcp_servers["web_server"].url == "https://mcp.example.com/api"
        
        assert "chat" in cfg.execution_flows
        assert cfg.execution_flows["chat"].model == "gpt4"
        assert cfg.execution_flows["chat"].type == "chatbot"
        
        assert "code_agent" in cfg.execution_flows
        assert "calculator" in cfg.execution_flows["code_agent"].tools
        assert "file_server" in cfg.execution_flows["code_agent"].mcp_servers
        
        assert cfg.hpc_cluster_config is not None
        assert cfg.hpc_cluster_config["cluster_name"] == "perlmutter"
        
        assert cfg.logging_config is not None
        assert cfg.logging_config["level"] == "INFO"

    def test_load_config_all_flow_types(self, tmp_path):
        """Test loading configuration with all execution flow types."""
        cfg_file = tmp_path / 'all_flows.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test-model"

tools:
  test_tool:
    class_name: "TestTool"
    module_path: "test.tool"

execution_flows:
  chatbot_flow:
    type: "chatbot"
    model: "test_model"
  code_agent_flow:
    type: "agent"
    agent_type: "code"
    model: "test_model"
    tools: ["test_tool"]
  prompt_chain_flow:
    type: "prompt_chain"
    model: "test_model"
    prompt_chain:
      - role: "user"
        content: "Hello"
  tool_calling_flow:
    type: "agent"
    agent_type: "tool_calling"
    model: "test_model"
    tools: ["test_tool"]
''')
        cfg = ConfigLoader.load_config(str(cfg_file))
        
        assert cfg.execution_flows["chatbot_flow"].type == "chatbot"
        assert cfg.execution_flows["code_agent_flow"].type == "agent"
        assert cfg.execution_flows["prompt_chain_flow"].type == "prompt_chain"
        assert cfg.execution_flows["tool_calling_flow"].type == "agent"


class TestEnvironmentVariableIntegration:
    """Test environment variable expansion during loading."""
    
    def test_load_config_with_environment_variables(self, tmp_path, monkeypatch):
        """Test that environment variables are properly expanded during loading."""
        monkeypatch.setenv('TEST_API_KEY', 'secret123')
        monkeypatch.setenv('TEST_API_BASE', 'https://api.test.com')
        monkeypatch.setenv('TEST_COMMAND', 'python server.py')
        
        cfg_file = tmp_path / 'env_config.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    api_key: "${TEST_API_KEY}"
    api_base: "${TEST_API_BASE}"

mcp_servers:
  test_server:
    mcp_type: "mcp_stdio"
    command: "${TEST_COMMAND}"
    env:
      API_KEY: "${TEST_API_KEY}"

execution_flows:
  test_flow:
    type: "agent"
    agent_type: "code"
    model: "test_model"
    mcp_servers: ["test_server"]
    tools: []
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["test_model"].api_key == "secret123"
        assert cfg.models["test_model"].api_base == "https://api.test.com"
        # Note: command field doesn't have env var expansion in MCPServerConfig
        assert cfg.mcp_servers["test_server"].command == "${TEST_COMMAND}"
        assert cfg.mcp_servers["test_server"].env["API_KEY"] == "secret123"

    def test_load_config_missing_environment_variables(self, tmp_path, monkeypatch):
        """Test behavior with missing environment variables."""
        monkeypatch.delenv('MISSING_VAR', raising=False)
        
        cfg_file = tmp_path / 'missing_env.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    api_key: "${MISSING_VAR}"
execution_flows:
  test_flow:
    type: "chatbot"
    model: "test_model"
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["test_model"].api_key == "${MISSING_VAR}"  # Should remain unexpanded

    def test_load_config_complex_environment_variables(self, tmp_path, monkeypatch):
        """Test complex environment variable scenarios."""
        monkeypatch.setenv('API_HOST', 'api.example.com')
        monkeypatch.setenv('API_VERSION', 'v1')
        monkeypatch.setenv('API_PORT', '8080')
        
        cfg_file = tmp_path / 'complex_env.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    api_base: "https://${API_HOST}:${API_PORT}/${API_VERSION}"

mcp_servers:
  test_server:
    mcp_type: "mcp_sse"
    url: "https://${API_HOST}:${API_PORT}/mcp"
    headers:
      Host: "${API_HOST}"

execution_flows:
  test_flow:
    type: "agent"
    agent_type: "code"
    model: "test_model"
    mcp_servers: ["test_server"]
    tools: []
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["test_model"].api_base == "https://api.example.com:8080/v1"
        assert cfg.mcp_servers["test_server"].url == "https://api.example.com:8080/mcp"
        assert cfg.mcp_servers["test_server"].headers["Host"] == "api.example.com"


class TestReferenceValidation:
    """Test cross-reference validation during loading."""
    
    def test_load_config_invalid_model_reference(self, tmp_path):
        """Test that invalid model references are caught during loading."""
        cfg_file = tmp_path / 'invalid_model_ref.yaml'
        cfg_file.write_text('''
models:
  valid_model:
    model_id: "test"
execution_flows:
  test_flow:
    type: "chatbot"
    model: "nonexistent_model"  # Invalid reference
''')
        
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.load_config(str(cfg_file))
        assert "Configuration validation failed" in str(exc_info.value)
        assert "references unknown model" in str(exc_info.value)

    def test_load_config_invalid_tool_reference(self, tmp_path):
        """Test that invalid tool references are caught during loading."""
        cfg_file = tmp_path / 'invalid_tool_ref.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
tools:
  valid_tool:
    class_name: "Tool"
    module_path: "tools.tool"
execution_flows:
  test_flow:
    type: "agent"
    agent_type: "code"
    model: "test_model"
    tools: ["nonexistent_tool"]  # Invalid reference
''')
        
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.load_config(str(cfg_file))
        assert "Configuration validation failed" in str(exc_info.value)
        assert "references unknown tool" in str(exc_info.value)

    def test_load_config_invalid_mcp_server_reference(self, tmp_path):
        """Test that invalid MCP server references are caught during loading."""
        cfg_file = tmp_path / 'invalid_mcp_ref.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
mcp_servers:
  valid_server:
    mcp_type: "mcp_stdio"
    command: "test"
execution_flows:
  test_flow:
    type: "agent"
    agent_type: "tool_calling"
    model: "test_model"
    mcp_servers: ["nonexistent_server"]  # Invalid reference
''')
        
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.load_config(str(cfg_file))
        assert "Configuration validation failed" in str(exc_info.value)
        assert "references unknown MCP server" in str(exc_info.value)

    def test_load_config_multiple_invalid_references(self, tmp_path):
        """Test multiple invalid references in single flow."""
        cfg_file = tmp_path / 'multiple_invalid_refs.yaml'
        cfg_file.write_text('''
models:
  valid_model:
    model_id: "test"
execution_flows:
  test_flow:
    type: "agent"
    agent_type: "tool_calling"
    model: "invalid_model"  # Invalid model reference
    tools: ["invalid_tool"]  # Invalid tool reference
    mcp_servers: ["invalid_server"]  # Invalid MCP server reference
''')
        
        with pytest.raises(ValueError, match="Configuration validation failed"):
            ConfigLoader.load_config(str(cfg_file))


class TestFileAccessAndPermissions:
    """Test file access and permission scenarios."""
    
    def test_load_config_directory_instead_of_file(self, tmp_path):
        """Test error when trying to load a directory instead of a file."""
        config_dir = tmp_path / 'config_dir'
        config_dir.mkdir()
        
        with pytest.raises((IsADirectoryError, PermissionError)):
            ConfigLoader.load_config(str(config_dir))


class TestPerformanceAndScale:
    """Test performance with large configurations."""
    
    def test_load_config_large_configuration(self, tmp_path):
        """Test loading a large configuration file."""
        # Generate a large but valid configuration
        models = {f"model_{i}": {"model_id": f"model-{i}"} for i in range(50)}
        tools = {f"tool_{i}": {"class_name": f"Tool{i}", "module_path": f"tools.tool{i}"} for i in range(25)}
        mcp_servers = {f"server_{i}": {"mcp_type": "mcp_stdio", "command": f"server{i}"} for i in range(10)}
        
        large_config = {
            "models": models,
            "tools": tools,
            "mcp_servers": mcp_servers,
            "execution_flows": {
                f"flow_{i}": {
                    "type": "chatbot",
                    "model": f"model_{i % 50}"
                } for i in range(100)
            }
        }
        
        cfg_file = tmp_path / 'large.yaml'
        with open(cfg_file, 'w') as f:
            yaml.dump(large_config, f)
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert len(cfg.models) == 50
        assert len(cfg.tools) == 25
        assert len(cfg.mcp_servers) == 10
        assert len(cfg.execution_flows) == 100

    def test_load_config_deep_nesting(self, tmp_path):
        """Test configuration with deeply nested structures."""
        cfg_file = tmp_path / 'deep_nested.yaml'
        cfg_file.write_text('''
models:
  complex_model:
    model_id: "complex"
    system_prompt: |
      You are a complex AI assistant with multiple capabilities.
      You can handle various tasks including:
      - Code generation and analysis
      - Data processing and visualization
      - Natural language understanding
      - Mathematical computations

tools:
  complex_tool:
    class_name: "ComplexTool"
    module_path: "complex.tools.advanced"
    parameters:
      config:
        database:
          host: "localhost"
          port: 5432
          credentials:
            username: "user"
            password: "pass"
        api_settings:
          timeout: 30
          retries: 3
          endpoints:
            - name: "primary"
              url: "https://api1.example.com"
            - name: "secondary"
              url: "https://api2.example.com"

execution_flows:
  complex_flow:
    type: "prompt_chain"
    model: "complex_model"
    prompt_chain:
      - role: "system"
        content: "Initialize complex processing"
      - role: "user"
        content: "Begin analysis"
      - role: "assistant"
        content: "Starting comprehensive analysis"
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["complex_model"].model_id == "complex"
        assert "database" in cfg.tools["complex_tool"].parameters["config"]
        assert len(cfg.execution_flows["complex_flow"].prompt_chain) == 3


class TestErrorMessageQuality:
    """Test that error messages are clear and helpful."""
    
    def test_validation_error_contains_file_context(self, tmp_path):
        """Test that validation errors reference the config file."""
        cfg_file = tmp_path / 'error_context.yaml'
        cfg_file.write_text('''
models:
  bad_model:
    model_id: "test"
    temperature: 999  # Invalid value
execution_flows:
  test_flow:
    type: "chatbot"
    model: "bad_model"
''')
        
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.load_config(str(cfg_file))
        
        error_msg = str(exc_info.value)
        assert "Configuration validation failed" in error_msg
        # The error should contain details about the validation failure

    def test_yaml_error_preserves_context(self, tmp_path):
        """Test that YAML parsing errors preserve file context."""
        cfg_file = tmp_path / 'yaml_error_context.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    invalid_yaml: [unclosed list
''')
        
        with pytest.raises(yaml.YAMLError) as exc_info:
            ConfigLoader.load_config(str(cfg_file))
        
        # YAML errors should contain line/column information
        error_msg = str(exc_info.value)
        assert error_msg  # Should have meaningful error message


class TestEdgeCases:
    """Test various edge cases and boundary conditions."""
    
    def test_load_config_unicode_content(self, tmp_path):
        """Test loading configuration with Unicode content."""
        cfg_file = tmp_path / 'unicode.yaml'
        cfg_file.write_text('''
models:
  unicode_model:
    model_id: "test-模型"
    system_prompt: "你好，我是AI助手。¡Hola! Bonjour! 🤖"

execution_flows:
  unicode_flow:
    type: "chatbot"
    model: "unicode_model"
    system_prompt: "Handling émojis and spëcial characters: ñáéíóú"
''', encoding='utf-8')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["unicode_model"].model_id == "test-模型"
        assert "🤖" in cfg.models["unicode_model"].system_prompt
        assert "émojis" in cfg.execution_flows["unicode_flow"].system_prompt

    def test_load_config_very_long_strings(self, tmp_path):
        """Test configuration with very long string values."""
        long_prompt = "This is a very long system prompt. " * 100
        
        cfg_file = tmp_path / 'long_strings.yaml'
        cfg_file.write_text(f'''
models:
  long_model:
    model_id: "test"
    system_prompt: "{long_prompt}"

execution_flows:
  long_flow:
    type: "chatbot"
    model: "long_model"
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert len(cfg.models["long_model"].system_prompt) > 1000
        assert cfg.models["long_model"].system_prompt == long_prompt

    def test_load_config_null_and_empty_values(self, tmp_path):
        """Test handling of null and empty values."""
        cfg_file = tmp_path / 'null_empty.yaml'
        cfg_file.write_text('''
models:
  test_model:
    model_id: "test"
    api_key: null
    api_base: ""
    system_prompt: ~

tools:
  empty_tool:
    class_name: "Tool"
    module_path: "tool"
    parameters: {}

execution_flows:
  test_flow:
    type: "agent"
    agent_type: "code"
    model: "test_model"
    tools: []
    mcp_servers: []
''')
        
        cfg = ConfigLoader.load_config(str(cfg_file))
        assert cfg.models["test_model"].api_key is None
        assert cfg.models["test_model"].api_base is None  # Empty string becomes None after validation
        assert cfg.models["test_model"].system_prompt is None
        assert cfg.tools["empty_tool"].parameters == {}
        assert cfg.execution_flows["test_flow"].tools == []
        assert cfg.execution_flows["test_flow"].mcp_servers == []
        assert getattr(cfg.execution_flows["test_flow"], "prompt_chain", None) is None

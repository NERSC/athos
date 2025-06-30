import os
import pytest

from athos.config import ConfigLoader
from athos.config.models import AthosConfig, ExecutionFlowType


def test_expand_env_var_success(monkeypatch):
    monkeypatch.setenv('FOO', 'foo_val')
    monkeypatch.setenv('BAR', 'bar_val')
    s = 'X${FOO}Y${BAR}Z'
    result = ConfigLoader._expand_env_var(s)
    assert result == 'Xfoo_valYbar_valZ'


def test_expand_env_var_missing(monkeypatch):
    monkeypatch.delenv('NOT_SET', raising=False)
    result = ConfigLoader._expand_env_var('${NOT_SET}')
    # Should return the original string unchanged when env var is not set
    assert result == '${NOT_SET}'


def test_expand_env_var_mixed_missing_and_present(monkeypatch):
    monkeypatch.setenv('PRESENT', 'value')
    monkeypatch.delenv('MISSING', raising=False)
    result = ConfigLoader._expand_env_var('${PRESENT}_${MISSING}_end')
    # Should expand present vars but leave missing ones unchanged
    assert result == 'value_${MISSING}_end'


def test_parse_config_minimal(monkeypatch):
    # Prepare environment for api_key expansion
    monkeypatch.setenv('API_KEY', 'key123')
    # Minimal config dict
    config_data = {
        'models': {
            'm1': {
                'model_id': 'id1',
                'api_key': '${API_KEY}',
                'api_base': ''
            }
        },
        'tools': {
            't1': {
                'class_name': 'C',
                'module_path': 'mod',
                'parameters': {'p': 1}
            }
        },
        'execution_flows': {
            'f1': {
                'type': 'chatbot',
                'model': 'm1',
                'tools': [],
                'prompt_chain': None,
                'system_prompt': 'hello',
                'max_iterations': 5
            }
        }
    }
    cfg = ConfigLoader._parse_config(config_data)
    # Validate types and values
    assert isinstance(cfg, AthosConfig)
    # Model config
    m1 = cfg.models.get('m1')
    assert m1.model_id == 'id1'
    assert m1.api_key == 'key123'
    assert m1.api_base == ''
    # Tool config
    t1 = cfg.tools.get('t1')
    assert t1.class_name == 'C'
    assert t1.module_path == 'mod'
    assert t1.parameters == {'p': 1}
    # Flow config
    f1 = cfg.execution_flows.get('f1')
    assert f1.name == 'f1'
    assert f1.type == ExecutionFlowType.CHATBOT
    assert f1.model == 'm1'
    assert f1.system_prompt == 'hello'
    assert f1.max_iterations == 5


def test_parse_config_invalid_flow_type():
    # Flow type unknown should raise ValueError
    config_data = {
        'models': {},
        'tools': {},
        'execution_flows': {
            'f2': {'type': 'invalid_type', 'model': 'm'}
        }
    }
    with pytest.raises(ValueError):
        ConfigLoader._parse_config(config_data)
    
def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        ConfigLoader.load_config('nonexistent_file.yaml')

def test_load_config_minimal_file(tmp_path):
    # Empty YAML should produce empty AthosConfig sections
    cfg_file = tmp_path / 'empty.yaml'
    cfg_file.write_text('{}')
    cfg = ConfigLoader.load_config(str(cfg_file))
    assert hasattr(cfg, 'models') and cfg.models == {}
    assert hasattr(cfg, 'tools') and cfg.tools == {}
    assert hasattr(cfg, 'execution_flows') and cfg.execution_flows == {}
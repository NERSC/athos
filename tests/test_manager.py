import asyncio
import pytest
import types

import athos.core.manager as manager_module
import athos.core.flows as flows_module
from athos.core.manager import AthosManager
from athos.config.models import (
    AthosConfig,
    ModelConfig,
    ToolConfig,
    ExecutionFlowConfig,
    ExecutionFlowType,
)


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeModel:
    def __init__(self, model_id: str, api_base=None, api_key=None):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key

    def __call__(self, messages, stop_sequences=None):
        return FakeResponse("fake response")


class DummyCodeAgent:
    def __init__(self, tools, model):
        self.tools = tools
        self.model = model

    def run(self, input_data: str) -> str:
        return f"Ran DummyCodeAgent with {input_data}"


class DummyToolCallingAgent:
    def __init__(self, tools, model):
        self.tools = tools
        self.model = model

    def run(self, input_data: str) -> str:
        return f"Ran DummyToolCallingAgent with {input_data}"


@pytest.fixture(autouse=True)
def patch_models_and_agents(monkeypatch):
    # Patch model and agent classes to use test fakes
    monkeypatch.setattr(manager_module, 'OpenAIServerModel', FakeModel)
    monkeypatch.setattr(flows_module, 'CodeAgent', DummyCodeAgent)
    monkeypatch.setattr(flows_module, 'ToolCallingAgent', DummyToolCallingAgent)


def build_manager():
    # Create a sample configuration with one model, one tool, and three flows
    models = {
        'mymodel': ModelConfig(name='mymodel', model_id='model1')
    }
    tools = {
        'simple': ToolConfig(
            name='simple',
            class_name='SimpleNamespace',
            module_path='types',
            parameters={'x': 1}
        )
    }
    execution_flows = {
        'chatflow': ExecutionFlowConfig(
            name='chatflow',
            type=ExecutionFlowType.CHATBOT,
            model='mymodel',
            tools=[],
            system_prompt='sys'
        ),
        'codeflow': ExecutionFlowConfig(
            name='codeflow',
            type=ExecutionFlowType.CODE_AGENT,
            model='mymodel',
            tools=['simple']
        ),
        'toolcallflow': ExecutionFlowConfig(
            name='toolcallflow',
            type=ExecutionFlowType.TOOL_CALLING_AGENT,
            model='mymodel',
            tools=['simple']
        ),
    }
    config = AthosConfig(
        models=models,
        tools=tools,
        execution_flows=execution_flows
    )
    return AthosManager(config)


def test_initialize_and_list_and_info():
    manager = build_manager()
    # Models and flows initialized
    assert set(manager.models.keys()) == {'mymodel'}
    assert isinstance(manager.models['mymodel'], FakeModel)
    assert set(manager.flows.keys()) == {'chatflow', 'codeflow', 'toolcallflow'}
    # list_flows
    flows_list = manager.list_flows()
    assert set(flows_list) == {'chatflow', 'codeflow', 'toolcallflow'}
    # get_flow_info for chatbot
    info = manager.get_flow_info('chatflow')
    assert info == {
        'name': 'chatflow',
        'type': ExecutionFlowType.CHATBOT.value,
        'model': 'mymodel',
        'tools': [],
        'has_prompt_chain': False
    }
    # get_flow_info for code agent
    info2 = manager.get_flow_info('codeflow')
    assert info2['name'] == 'codeflow'
    assert info2['type'] == ExecutionFlowType.CODE_AGENT.value
    assert info2['model'] == 'mymodel'
    assert info2['tools'] == ['simple']
    assert info2['has_prompt_chain'] is False
    # Unknown flow info raises
    with pytest.raises(ValueError):
        manager.get_flow_info('unknown')


def test_execute_flows():
    manager = build_manager()
    # Chatbot flow execution
    result_chat = asyncio.run(manager.execute_flow('chatflow', 'hello'))
    assert result_chat == 'fake response'
    # Code agent flow execution
    result_code = asyncio.run(manager.execute_flow('codeflow', 'run it'))
    assert result_code == 'Ran DummyCodeAgent with run it'
    # Tool calling agent flow execution
    result_toolcall = asyncio.run(manager.execute_flow('toolcallflow', 'task'))
    assert result_toolcall == 'Ran DummyToolCallingAgent with task'
    # Unknown flow execution raises
    with pytest.raises(ValueError):
        asyncio.run(manager.execute_flow('noflow', 'x'))


def test_load_tool_caching_and_failure():
    # Manager with no initial config
    empty_config = AthosConfig(models={}, tools={}, execution_flows={})
    manager = AthosManager(empty_config)
    # Successful load and caching
    tc = ToolConfig(
        name='simple2',
        class_name='SimpleNamespace',
        module_path='types',
        parameters={'a': 10, 'b': 20}
    )
    tool1 = manager._load_tool(tc)
    assert isinstance(tool1, types.SimpleNamespace)
    assert tool1.a == 10 and tool1.b == 20
    # Cached on second load
    tool2 = manager._load_tool(tc)
    assert tool2 is tool1
    # Failure on bad module
    bad_tc = ToolConfig(
        name='bad',
        class_name='X',
        module_path='nonexistent',
        parameters={}
    )
    with pytest.raises(ModuleNotFoundError):
        manager._load_tool(bad_tc)
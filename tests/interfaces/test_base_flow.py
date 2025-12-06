import pytest

from athos.interfaces.base_flow import BaseFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession


class IncompleteFlow(BaseFlow):
    name = "incomplete"
    config_class = object
    framework = object

    @classmethod
    async def create(cls, flow_config, athos_config):
        return cls()

    async def execute(self, input: FlowInput) -> FlowOutput:  # pragma: no cover - used for error path
        return await super().execute(input)


class EchoFlow(BaseFlow):
    name = "echo"
    config_class = object
    framework = object

    @classmethod
    async def create(cls, flow_config, athos_config):
        return cls()

    async def execute(self, input: FlowInput) -> FlowOutput:
        return FlowOutput(content=input.message.content)


class StreamingFlow(EchoFlow):
    name = "streaming"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    @classmethod
    async def create(cls, flow_config, athos_config):
        return cls()


@pytest.fixture
def flow_input() -> FlowInput:
    session = FlowSession(session_id="session", user_id="user")
    return FlowInput(message="hello", session=session, mode=ExecutionMode.SYNC)


@pytest.mark.asyncio
async def test_execute_raises_not_implemented(flow_input: FlowInput) -> None:
    flow = IncompleteFlow()
    with pytest.raises(NotImplementedError):
        await flow.execute(flow_input)


@pytest.mark.asyncio
async def test_stream_calls_execute(flow_input: FlowInput) -> None:
    flow = EchoFlow()
    results = [result async for result in flow.stream(flow_input)]

    assert len(results) == 1
    assert results[0].content == "hello"


def test_can_stream_checks_supported_modes() -> None:
    assert not EchoFlow().can_stream()
    assert StreamingFlow().can_stream()

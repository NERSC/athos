import pytest

from athos.models import ExecutionMode, FlowOutput, FlowRequest, FlowResult


def test_flow_request_serialization():
    request = FlowRequest(
        request_id="req-1",
        flow_name="demo",
        message="Run",
        session_id="sess-1",
        user_id="user-1",
        mode=ExecutionMode.SYNC,
        metadata={"source": "test"},
    )

    dumped = request.model_dump()
    assert dumped["flow_name"] == "demo"
    assert dumped["metadata"] == {"source": "test"}
    assert "timestamp" in dumped


def test_flow_result_contains_output_metadata():
    output = FlowOutput(content="done")
    result = FlowResult(
        request_id="req-1",
        success=True,
        output=output,
        error=None,
        execution_time=0.5,
        metadata={"tokens": 10},
    )

    dumped = result.model_dump()
    assert dumped["success"] is True
    assert dumped["metadata"]["tokens"] == 10
    assert dumped["output"]["content"] == "done"


def test_flow_request_is_immutable():
    request = FlowRequest(
        request_id="req-2",
        flow_name="demo",
        message="Run",
        session_id="sess-2",
        user_id="user-2",
        mode=ExecutionMode.SYNC,
    )

    with pytest.raises(Exception):
        request.flow_name = "other"


def test_flow_result_is_immutable():
    result = FlowResult(
        request_id="req-3",
        success=False,
        output=None,
        error="boom",
        execution_time=1.2,
    )

    with pytest.raises(Exception):
        result.success = True

import pytest

from athos.models import Artifact, ExecutionMode, FlowInput, FlowOutput, FlowSession


def test_flow_input_serialization_round_trip():
    session = FlowSession(session_id="sess-1", user_id="user-1")
    flow_input = FlowInput(
        message="Hello",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={"intent": "greeting"},
    )

    dumped = flow_input.model_dump()
    assert dumped["message"] == "Hello"
    assert dumped["metadata"] == {"intent": "greeting"}
    assert dumped["session"]["session_id"] == "sess-1"


def test_flow_output_supports_artifacts_and_metadata():
    artifact = Artifact(type="image", path="/tmp/plot.png", display_name="Plot")
    flow_output = FlowOutput(
        content="Here is your plot",
        artifacts=[artifact],
        metadata={"tokens": 42},
    )

    dumped = flow_output.model_dump()
    assert dumped["content"] == "Here is your plot"
    assert dumped["artifacts"][0]["type"] == "image"
    assert dumped["metadata"]["tokens"] == 42


def test_artifacts_are_immutable():
    artifact = Artifact(type="file")
    with pytest.raises(Exception):
        artifact.type = "image"


def test_flow_output_has_independent_artifact_lists():
    first = FlowOutput(content="one")
    second = FlowOutput(content="two")

    first.artifacts.append(Artifact(type="file", path="/tmp/file.txt"))

    assert len(first.artifacts) == 1
    assert len(second.artifacts) == 0


def test_flow_input_is_immutable():
    session = FlowSession(session_id="sess-2", user_id="user-2")
    flow_input = FlowInput(message="hi", session=session, mode=ExecutionMode.SYNC)

    with pytest.raises(Exception):
        flow_input.message = "bye"

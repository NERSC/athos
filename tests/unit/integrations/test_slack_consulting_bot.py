import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from anyio.from_thread import start_blocking_portal

from athos.integrations.slack.consulting_bot import AthosConsultingSlackAdapter, slack_session_id
from athos.integrations.slack.runtime import SlackMessageRequest


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.loop_ids = []
        self.cleanup_loop_id = None
        self._execute_lock = asyncio.Lock()

    async def execute(self, **kwargs):
        async with self._execute_lock:
            self.calls.append(kwargs)
            self.loop_ids.append(id(asyncio.get_running_loop()))
            await asyncio.sleep(0.01)
            return self.result

    async def cleanup(self):
        self.cleanup_loop_id = id(asyncio.get_running_loop())


@pytest.fixture
def portal():
    with start_blocking_portal(backend="asyncio") as value:
        yield value


def test_consulting_adapter_uses_the_slack_thread_as_session(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="Consultant answer", metadata={}),
        )
    )
    adapter = AthosConsultingSlackAdapter(runner, portal=portal)
    slack_request = SlackMessageRequest(
        channel="C123",
        thread_ts="171234.000100",
        event_ts="171234.000200",
        user_id="U123",
        question="Please check INC0012345",
    )

    response = adapter.handle_question(slack_request)

    assert slack_session_id(slack_request) == "C123:171234.000100"
    assert runner.calls == [
        {
            "flow_name": "lang_hpc_consulting_agent",
            "message": "Please check INC0012345",
            "session_id": "C123:171234.000100",
            "user_id": "U123",
            "interface": "slack",
            "metadata": {"slack_channel": "C123", "slack_thread_ts": "171234.000100"},
        }
    ]
    assert response.text == "Consultant answer"
    assert response.blocks[1]["elements"][0]["action_id"] == "feedback_up"


def test_consulting_adapter_splits_long_answers_from_feedback_controls(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="x" * 3001, metadata={}),
        )
    )
    adapter = AthosConsultingSlackAdapter(runner, portal=portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert response.blocks is None
    assert response.followup_posts[0].text == "Was this response helpful?"
    assert response.followup_posts[0].blocks[0]["type"] == "actions"


def test_consulting_adapter_returns_a_safe_message_when_the_flow_fails(portal):
    runner = FakeRunner(SimpleNamespace(success=False, output=None, error="credential details must not reach Slack"))
    adapter = AthosConsultingSlackAdapter(runner, portal=portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert "could not complete" in response.text
    assert "credential details" not in response.text


def test_consulting_adapter_returns_a_safe_message_for_error_output(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(
                content="Error: credential details must not reach Slack",
                metadata={"error": True},
            ),
        )
    )
    adapter = AthosConsultingSlackAdapter(runner, portal=portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert "could not complete" in response.text
    assert "credential details" not in response.text


def test_consulting_adapter_uses_one_event_loop_for_concurrent_requests(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="Consultant answer", metadata={}),
        )
    )
    adapter = AthosConsultingSlackAdapter(runner, portal=portal)
    requests = [
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "first"),
        SlackMessageRequest("C123", "171234.000300", "171234.000400", "U456", "second"),
    ]

    with ThreadPoolExecutor(max_workers=2) as callers:
        responses = list(callers.map(adapter.handle_question, requests))

    portal.call(runner.cleanup)

    assert [response.text for response in responses] == [
        "Consultant answer",
        "Consultant answer",
    ]
    assert len(set(runner.loop_ids)) == 1
    assert runner.cleanup_loop_id == runner.loop_ids[0]

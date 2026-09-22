import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from anyio.from_thread import start_blocking_portal

from athos.integrations.slack.consulting_bot import (
    BUTTON_VALUE_MAX_LEN,
    PRIVATE_METADATA_MAX_LEN,
    UNAUTHORIZED_USER_TEXT,
    AthosConsultingSlackAdapter,
    slack_session_id,
)
from athos.integrations.slack.runtime import (
    REQUEST_FAILURE_TEXT,
    SlackInteractionRequest,
    SlackMessageRequest,
)


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.loop_ids = []
        self.cleanup_loop_id = None
        self.active_calls = 0
        self.max_active_calls = 0

    async def execute(self, **kwargs):
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        try:
            self.calls.append(kwargs)
            self.loop_ids.append(id(asyncio.get_running_loop()))
            await asyncio.sleep(0.05)
            return self.result
        finally:
            self.active_calls -= 1

    async def cleanup(self):
        self.cleanup_loop_id = id(asyncio.get_running_loop())


@pytest.fixture
def portal():
    with start_blocking_portal(backend="asyncio") as value:
        yield value


def make_adapter(runner, portal):
    return AthosConsultingSlackAdapter(
        runner,
        portal=portal,
        allowed_users={"U123", "U456"},
    )


def test_consulting_adapter_uses_the_slack_thread_as_session(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="Consultant answer", metadata={}),
        )
    )
    adapter = make_adapter(runner, portal)
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


def test_consulting_adapter_rejects_users_outside_the_allowlist(portal):
    runner = FakeRunner(
        SimpleNamespace(success=True, output=SimpleNamespace(content="secret", metadata={}))
    )
    adapter = make_adapter(runner, portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U999", "help")
    )

    assert response.text == UNAUTHORIZED_USER_TEXT
    assert runner.calls == []


def test_consulting_adapter_requires_an_allowlist(portal):
    with pytest.raises(ValueError, match="ATHOS_SLACK_ALLOWED_USERS"):
        AthosConsultingSlackAdapter(FakeRunner(None), portal=portal, allowed_users=[])


def test_consulting_adapter_splits_long_answers_from_feedback_controls(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="x" * 3001, metadata={}),
        )
    )
    adapter = make_adapter(runner, portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert response.blocks is None
    assert response.followup_posts[0].text == "Was this response helpful?"
    assert response.followup_posts[0].blocks[0]["type"] == "actions"
    value = response.followup_posts[0].blocks[0]["elements"][0]["value"]
    payload = json.loads(value)
    assert len(value) <= BUTTON_VALUE_MAX_LEN
    assert payload["detached"] is True

    interaction = adapter.handle_interaction(
        SlackInteractionRequest(
            "C123",
            "171234.000100",
            "171234.000300",
            "U123",
            "feedback_up",
            value,
            context={"message": {"text": "Was this response helpful?"}},
        )
    )

    assert interaction.replace_original.text == "Thanks for the feedback! 👍"
    assert interaction.replace_original.blocks is None


def test_feedback_keeps_the_full_slack_message_and_valid_metadata(portal):
    answer = '"quoted"\n' * 250
    runner = FakeRunner(
        SimpleNamespace(success=True, output=SimpleNamespace(content=answer, metadata={}))
    )
    adapter = make_adapter(runner, portal)
    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "q" * 500)
    )
    value = response.blocks[1]["elements"][0]["value"]

    interaction = adapter.handle_interaction(
        SlackInteractionRequest(
            "C123",
            "171234.000100",
            "171234.000300",
            "U123",
            "feedback_down",
            value,
            context={"message": {"text": response.text}},
        )
    )

    assert "response_text" not in json.loads(value)
    assert interaction.replace_original.text == response.text
    metadata = interaction.open_view["private_metadata"]
    assert len(metadata) <= PRIVATE_METADATA_MAX_LEN
    assert json.loads(metadata)["session_id"] == "C123:171234.000100"


def test_consulting_adapter_returns_a_safe_message_when_the_flow_fails(portal):
    runner = FakeRunner(SimpleNamespace(success=False, output=None, error="credential details must not reach Slack"))
    adapter = make_adapter(runner, portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert response.text == REQUEST_FAILURE_TEXT
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
    adapter = make_adapter(runner, portal)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert response.text == REQUEST_FAILURE_TEXT
    assert "credential details" not in response.text


def test_consulting_adapter_uses_one_event_loop_for_concurrent_requests(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="Consultant answer", metadata={}),
        )
    )
    adapter = make_adapter(runner, portal)
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
    assert runner.max_active_calls == 2


def test_consulting_adapter_serializes_requests_in_the_same_slack_thread(portal):
    runner = FakeRunner(
        SimpleNamespace(
            success=True,
            output=SimpleNamespace(content="Consultant answer", metadata={}),
        )
    )
    adapter = make_adapter(runner, portal)
    requests = [
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "first"),
        SlackMessageRequest("C123", "171234.000100", "171234.000300", "U456", "second"),
    ]

    with ThreadPoolExecutor(max_workers=2) as callers:
        responses = list(callers.map(adapter.handle_question, requests))

    assert [response.text for response in responses] == [
        "Consultant answer",
        "Consultant answer",
    ]
    assert runner.max_active_calls == 1

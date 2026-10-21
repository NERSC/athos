import sqlite3
from types import SimpleNamespace

from athos.integrations.slack.consulting_bot import (
    SANDBOX_QA_PAIRS,
    AthosConsultingSlackAdapter,
    create_sandbox_adapter,
    slack_session_id,
)
from athos.integrations.slack.feedback import FeedbackStore
from athos.integrations.slack.runtime import SlackMessageRequest


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def execute(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def test_consulting_adapter_uses_the_slack_thread_as_session():
    runner = FakeRunner(SimpleNamespace(success=True, output=SimpleNamespace(content="Consultant answer")))
    adapter = AthosConsultingSlackAdapter(runner)
    request = SlackMessageRequest(
        channel="C123",
        thread_ts="171234.000100",
        event_ts="171234.000200",
        user_id="U123",
        question="Please check INC0012345",
    )

    response = adapter.handle_question(request)

    assert slack_session_id(request) == "C123:171234.000100"
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


def test_consulting_adapter_splits_long_answers_from_feedback_controls():
    runner = FakeRunner(SimpleNamespace(success=True, output=SimpleNamespace(content="x" * 3001)))
    adapter = AthosConsultingSlackAdapter(runner)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert response.blocks is None
    assert response.followup_posts[0].text == "Was this response helpful?"
    assert response.followup_posts[0].blocks[0]["type"] == "actions"


def test_consulting_adapter_returns_a_safe_message_when_the_flow_fails():
    runner = FakeRunner(SimpleNamespace(success=False, output=None, error="credential details must not reach Slack"))
    adapter = AthosConsultingSlackAdapter(runner)

    response = adapter.handle_question(
        SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "help")
    )

    assert "could not complete" in response.text
    assert "credential details" not in response.text



def test_sandbox_replies_with_selected_answer_and_records_note(tmp_path, monkeypatch, capsys):
    selected_question, selected_answer = SANDBOX_QA_PAIRS[2]
    monkeypatch.setattr("athos.integrations.slack.consulting_bot.random.choice", lambda pairs: pairs[2])
    db_path = tmp_path / "feedback.db"
    adapter = create_sandbox_adapter(FeedbackStore(db_path))
    request = SlackMessageRequest("C123", "171234.000100", "171234.000200", "U123", "My query")

    response = adapter.handle_question(request)

    assert response.text == selected_answer
    output = capsys.readouterr().out
    assert "My query" in output
    assert selected_question in output
    assert selected_answer in output
    with sqlite3.connect(db_path) as connection:
        note = connection.execute(
            "SELECT kind, question, response_text, comment FROM slack_feedback"
        ).fetchone()
    assert note == ("sandbox_selection", "My query", selected_answer, f"Selected example question: {selected_question}")

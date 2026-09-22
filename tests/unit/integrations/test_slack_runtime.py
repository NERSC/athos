from unittest.mock import Mock

from athos.integrations.slack.runtime import (
    REQUEST_FAILURE_TEXT,
    SlackMessageRequest,
    SlackMessageResponse,
    _handle_message_request,
    _post_response,
)


class FakeWebClient:
    def __init__(self):
        self.calls = []
        self.events = []

    def chat_postMessage(self, **kwargs):
        self.calls.append(kwargs)
        self.events.append("post")
        return {"ts": "123.456"}

    def reactions_add(self, **kwargs):
        self.events.append(("reaction_add", kwargs))

    def reactions_remove(self, **kwargs):
        self.events.append(("reaction_remove", kwargs))


def test_runtime_drops_invalid_long_blocks_and_delivers_the_answer():
    client = FakeWebClient()
    answer = "x" * 3501
    response = SlackMessageResponse(
        text=answer,
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": answer}}],
    )

    _post_response(client, channel="C123", thread_ts="123.000", response=response)

    assert len(client.calls) == 2
    assert all("blocks" not in call for call in client.calls)
    assert client.calls[0]["thread_ts"] == "123.000"


def test_runtime_logs_handler_errors_without_exposing_details(monkeypatch):
    class FailingAdapter:
        def handle_question(self, request):
            raise RuntimeError("credential details must not reach Slack")

    client = FakeWebClient()
    request = SlackMessageRequest("C123", "123.000", "123.001", "U123", "help")
    log_exception = Mock()
    monkeypatch.setattr("athos.integrations.slack.runtime.logger.exception", log_exception)

    _handle_message_request(FailingAdapter(), client, request)

    log_exception.assert_called_once_with("Failed to handle Slack message request")
    assert client.calls[0]["text"] == REQUEST_FAILURE_TEXT
    assert [event[0] if isinstance(event, tuple) else event for event in client.events] == [
        "reaction_add",
        "post",
        "reaction_remove",
    ]


def test_runtime_marks_a_question_as_processing_until_the_reply_is_posted():
    class Adapter:
        def handle_question(self, request):
            return SlackMessageResponse("answer")

    client = FakeWebClient()
    request = SlackMessageRequest("C123", "123.000", "123.001", "U123", "help")

    _handle_message_request(Adapter(), client, request)

    assert client.events == [
        (
            "reaction_add",
            {
                "channel": "C123",
                "name": "hourglass_flowing_sand",
                "timestamp": "123.001",
            },
        ),
        "post",
        (
            "reaction_remove",
            {
                "channel": "C123",
                "name": "hourglass_flowing_sand",
                "timestamp": "123.001",
            },
        ),
    ]

from athos.integrations.slack.runtime import SlackMessageResponse, _post_response


class FakeWebClient:
    def __init__(self):
        self.calls = []

    def chat_postMessage(self, **kwargs):
        self.calls.append(kwargs)
        return {"ts": "123.456"}


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

from athos.integrations.slack.runtime import (
    PENDING_REACTION,
    SlackMessageResponse,
    _post_response,
    _process_interaction,
    _set_pending_reaction,
)


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


class ReactionClient:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def reactions_add(self, **kwargs):
        self.calls.append(("add", kwargs))
        if self.fail:
            raise RuntimeError("already_reacted")

    def reactions_remove(self, **kwargs):
        self.calls.append(("remove", kwargs))


def test_pending_reaction_is_added_and_removed_on_the_question():
    client = ReactionClient()

    _set_pending_reaction(client, "C123", "100.001", add=True)
    _set_pending_reaction(client, "C123", "100.001", add=False)

    expected = {"channel": "C123", "name": PENDING_REACTION, "timestamp": "100.001"}
    assert client.calls == [("add", expected), ("remove", expected)]


def test_pending_reaction_skips_slash_commands_and_ignores_slack_errors():
    client = ReactionClient(fail=True)

    _set_pending_reaction(client, "C123", None, add=True)
    _set_pending_reaction(client, "C123", "100.001", add=True)

    assert [kind for kind, _ in client.calls] == ["add"]


class InteractionClient(ReactionClient):
    def chat_update(self, **kwargs):
        self.calls.append(("update", kwargs))


class SlowActionAdapter:
    pending_actions = frozenset({"take_notes"})

    def __init__(self, client):
        self.client = client

    def handle_interaction(self, request):
        # The reaction must already be on the message while the action runs.
        assert [kind for kind, _ in self.client.calls] == ["add"]
        return None


def _block_action(action_id):
    return {
        "type": "block_actions",
        "actions": [{"action_id": action_id, "value": "{}"}],
        "channel": {"id": "C123"},
        "container": {"message_ts": "200.002"},
        "message": {"ts": "200.002", "thread_ts": "100.000"},
        "user": {"id": "U1"},
    }


def test_slow_action_shows_pending_reaction_on_clicked_message():
    client = InteractionClient()

    _process_interaction(SlowActionAdapter(client), client, _block_action("take_notes"))

    expected = {"channel": "C123", "name": PENDING_REACTION, "timestamp": "200.002"}
    assert client.calls == [("add", expected), ("remove", expected)]


def test_fast_action_does_not_show_pending_reaction():
    client = InteractionClient()
    adapter = SlowActionAdapter(client)
    adapter.handle_interaction = lambda request: None

    _process_interaction(adapter, client, _block_action("feedback_up"))

    assert client.calls == []

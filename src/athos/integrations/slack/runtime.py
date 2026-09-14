"""Reusable Slack Socket Mode plumbing for ATHOS integrations."""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


MAX_MESSAGE_LEN = 3500
MAX_BLOCK_TEXT_LEN = 3000
DEDUP_TTL_SECONDS = 120.0


@dataclass(slots=True)
class SlackMessageRequest:
    channel: str
    thread_ts: str | None
    event_ts: str | None
    user_id: str | None
    question: str
    raw_text: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SlackMessagePost:
    text: str
    blocks: list[dict[str, Any]] | None = None
    thread_ts: str | None = None
    channel: str | None = None


@dataclass(slots=True)
class SlackMessageResponse:
    text: str
    blocks: list[dict[str, Any]] | None = None
    followup_posts: list[SlackMessagePost] = field(default_factory=list)
    terminal_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SlackInteractionRequest:
    channel: str
    thread_ts: str | None
    message_ts: str | None
    user_id: str | None
    action_id: str
    action_value: str | None
    trigger_id: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SlackInteractionResponse:
    replace_original: SlackMessagePost | None = None
    thread_posts: list[SlackMessagePost] = field(default_factory=list)
    open_view: dict[str, Any] | None = None
    terminal_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SlackViewSubmissionRequest:
    user_id: str | None
    callback_id: str | None
    private_metadata: str
    values: dict[str, Any] = field(default_factory=dict)
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SlackViewSubmissionResponse:
    thread_posts: list[SlackMessagePost] = field(default_factory=list)
    terminal_fields: dict[str, Any] = field(default_factory=dict)


class SlackAppAdapter(Protocol):
    app_name: str
    empty_prompt: str

    def handle_question(self, request: SlackMessageRequest) -> SlackMessageResponse: ...
    def handle_interaction(self, request: SlackInteractionRequest) -> SlackInteractionResponse | None: ...
    def handle_view_submission(self, request: SlackViewSubmissionRequest) -> SlackViewSubmissionResponse | None: ...


class FunctionSlackAdapter:
    """Adapt functions to the Slack runtime protocol."""

    def __init__(
        self,
        handler: Callable[[SlackMessageRequest], str | SlackMessageResponse],
        *,
        app_name: str,
        empty_prompt: str = "Ask me a question and I will respond in this thread.",
        on_interaction: Callable[[SlackInteractionRequest], SlackInteractionResponse | None] | None = None,
        on_view_submission: Callable[[SlackViewSubmissionRequest], SlackViewSubmissionResponse | None] | None = None,
    ) -> None:
        self._handler = handler
        self._on_interaction = on_interaction
        self._on_view_submission = on_view_submission
        self.app_name = app_name
        self.empty_prompt = empty_prompt

    def handle_question(self, request: SlackMessageRequest) -> SlackMessageResponse:
        response = self._handler(request)
        return response if isinstance(response, SlackMessageResponse) else SlackMessageResponse(text=str(response))

    def handle_interaction(self, request: SlackInteractionRequest) -> SlackInteractionResponse | None:
        return self._on_interaction(request) if self._on_interaction else None

    def handle_view_submission(self, request: SlackViewSubmissionRequest) -> SlackViewSubmissionResponse | None:
        return self._on_view_submission(request) if self._on_view_submission else None


def flatten_input_values(values: dict[str, Any]) -> dict[str, str]:
    return {
        action_id: (state.get("value") or "")
        for block in (values or {}).values()
        for action_id, state in (block or {}).items()
        if isinstance(state, dict)
    }


def clean_question(text: str, bot_user_id: str) -> str:
    text = re.sub(rf"<@{re.escape(bot_user_id)}>", "", text or "")
    return " ".join(re.sub(r"<@[^>]+>", "", text).split())


def should_reply(event: dict[str, Any], bot_user_id: str) -> bool:
    if event.get("type") == "app_mention":
        return True
    if event.get("type") != "message" or event.get("subtype") or event.get("bot_id"):
        return False
    return event.get("channel_type") == "im" or f"<@{bot_user_id}>" in event.get("text", "")


def _import_slack():
    try:
        from slack_sdk import WebClient
        from slack_sdk.socket_mode import SocketModeClient
        from slack_sdk.socket_mode.response import SocketModeResponse
    except ImportError as exc:
        raise SystemExit("slack-sdk is required; install ATHOS with `pip install -e '.[slack]'`.") from exc
    return WebClient, SocketModeClient, SocketModeResponse


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _split_text(text: str) -> list[str]:
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]
    result: list[str] = []
    remaining = text
    while len(remaining) > MAX_MESSAGE_LEN:
        split_at = max(remaining.rfind("\n", 0, MAX_MESSAGE_LEN), remaining.rfind(" ", 0, MAX_MESSAGE_LEN))
        split_at = split_at if split_at >= MAX_MESSAGE_LEN // 2 else MAX_MESSAGE_LEN
        result.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return result + ([remaining] if remaining else [])


def _post(web_client, *, channel: str, thread_ts: str | None, post: SlackMessagePost) -> str | None:
    kwargs: dict[str, Any] = {"channel": post.channel or channel, "text": post.text}
    if post.thread_ts or thread_ts:
        kwargs["thread_ts"] = post.thread_ts or thread_ts
    if post.blocks:
        kwargs["blocks"] = post.blocks
    response = web_client.chat_postMessage(**kwargs)
    return response.get("ts")


def _blocks_within_text_limits(value: object) -> bool:
    """Return whether every Slack text object stays within Block Kit's limit."""
    if isinstance(value, dict):
        if value.get("type") in {"mrkdwn", "plain_text"}:
            text = value.get("text")
            if isinstance(text, str) and len(text) > MAX_BLOCK_TEXT_LEN:
                return False
        return all(_blocks_within_text_limits(child) for child in value.values())
    if isinstance(value, list):
        return all(_blocks_within_text_limits(child) for child in value)
    return True


def _post_response(web_client, *, channel: str, thread_ts: str | None, response: SlackMessageResponse) -> str | None:
    if response.blocks and _blocks_within_text_limits(response.blocks):
        return _post(web_client, channel=channel, thread_ts=thread_ts, post=SlackMessagePost(response.text, response.blocks))
    posted_ts = None
    for index, part in enumerate(_split_text(response.text)):
        chunk_ts = _post(
            web_client,
            channel=channel,
            thread_ts=thread_ts,
            post=SlackMessagePost(part if index == 0 else f"(continued)\n{part}"),
        )
        if posted_ts is None:
            posted_ts = chunk_ts
    return posted_ts


def run_socket_mode_app(adapter: SlackAppAdapter) -> None:
    """Connect an adapter to Slack Socket Mode and dispatch requests in threads."""
    WebClient, SocketModeClient, SocketModeResponse = _import_slack()
    web_client = WebClient(token=_require_env("SLACK_BOT_TOKEN"))
    auth = web_client.auth_test()
    bot_user_id = auth["user_id"]
    socket_client = SocketModeClient(app_token=_require_env("SLACK_APP_TOKEN"), web_client=web_client)
    recent: dict[str, float] = {}
    recent_lock = threading.Lock()

    def handle_request(request: SlackMessageRequest) -> None:
        try:
            response = adapter.handle_question(request)
            posted_ts = _post_response(web_client, channel=request.channel, thread_ts=request.thread_ts, response=response)
            for post in response.followup_posts:
                _post(web_client, channel=request.channel, thread_ts=post.thread_ts or request.thread_ts or posted_ts, post=post)
        except Exception as exc:  # noqa: BLE001
            _post_response(web_client, channel=request.channel, thread_ts=request.thread_ts, response=SlackMessageResponse(f":warning: I hit an error while answering this question:\n`{exc}`"))

    def process(client, envelope) -> None:
        if envelope.type not in {"events_api", "interactive"}:
            return
        client.send_socket_mode_response(SocketModeResponse(envelope_id=envelope.envelope_id))
        payload = envelope.payload
        if envelope.type == "interactive":
            threading.Thread(
                target=_process_interaction,
                args=(adapter, web_client, payload),
                daemon=True,
            ).start()
            return
        event = payload.get("event", {})
        if not should_reply(event, bot_user_id) or not event.get("channel"):
            return
        event_key = payload.get("event_id") or event.get("client_msg_id") or f"{event.get('channel')}:{event.get('ts')}"
        now = time.time()
        with recent_lock:
            recent.update({key: value for key, value in recent.items() if now - value <= DEDUP_TTL_SECONDS})
            if event_key in recent:
                return
            recent[event_key] = now
        thread_ts = event.get("thread_ts") or event.get("ts")
        question = clean_question(event.get("text", ""), bot_user_id)
        if not question:
            _post_response(web_client, channel=event["channel"], thread_ts=thread_ts, response=SlackMessageResponse(adapter.empty_prompt))
            return
        request = SlackMessageRequest(event["channel"], thread_ts, event.get("ts"), event.get("user"), question, event.get("text"), {"payload": payload, "event": event})
        threading.Thread(target=handle_request, args=(request,), daemon=True).start()

    socket_client.socket_mode_request_listeners.append(process)
    socket_client.connect()
    print(f"{adapter.app_name} Slack app online as {auth.get('user', adapter.app_name)} ({bot_user_id})")
    while True:
        time.sleep(1)


def _process_interaction(adapter: SlackAppAdapter, web_client, payload: dict[str, Any]) -> None:
    if payload.get("type") == "view_submission":
        view = payload.get("view", {})
        response = adapter.handle_view_submission(SlackViewSubmissionRequest((payload.get("user") or {}).get("id"), view.get("callback_id"), view.get("private_metadata", ""), (view.get("state") or {}).get("values", {}), payload))
        if response:
            for post in response.thread_posts:
                _post(web_client, channel=post.channel or "", thread_ts=post.thread_ts, post=post)
        return
    if payload.get("type") != "block_actions" or not payload.get("actions"):
        return
    action, message, container = payload["actions"][0], payload.get("message", {}), payload.get("container", {})
    channel = (payload.get("channel") or {}).get("id")
    if not channel:
        return
    request = SlackInteractionRequest(channel, message.get("thread_ts") or container.get("thread_ts") or container.get("message_ts"), container.get("message_ts") or message.get("ts"), (payload.get("user") or {}).get("id"), action.get("action_id", ""), action.get("value"), payload.get("trigger_id"), payload, {"message": message})
    response = adapter.handle_interaction(request)
    if response is None:
        return
    if response.open_view and request.trigger_id:
        web_client.views_open(trigger_id=request.trigger_id, view=response.open_view)
    if response.replace_original and request.message_ts:
        kwargs: dict[str, Any] = {"channel": channel, "ts": request.message_ts, "text": response.replace_original.text}
        if response.replace_original.blocks:
            kwargs["blocks"] = response.replace_original.blocks
        web_client.chat_update(**kwargs)
    for post in response.thread_posts:
        _post(web_client, channel=post.channel or channel, thread_ts=post.thread_ts or request.thread_ts or request.message_ts, post=post)

"""Drive a Slack adapter from a local web page instead of Slack.

SandboxApp turns what the page sends (a message, a button click, a modal
submit) into the event and interaction payloads Slack would deliver, and
hands them to the Slack runtime's own handlers with a SandboxWorkspace as
the web client. Replies, thread history, reactions, message updates and
modals all go through the same code as in production; only Slack itself is
replaced.

serve() starts a small HTTP server for the page. The page polls /api/state
and keeps nothing itself, and the workspace lives in memory, so every start
begins with an empty channel.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any

from ..runtime import (
    SlackAppAdapter,
    SlackMessageRequest,
    SlackMessageResponse,
    _handle_message_request,
    _post_response,
    _process_interaction,
    clean_question,
    read_thread_history,
    should_reply,
)
from .workspace import BOT_NAME, BOT_USER_ID, CHANNEL_ID, CHANNEL_NAME, SandboxWorkspace

DEFAULT_USER_ID = "USANDBOX"
_MENTION_RE = re.compile(rf"@{BOT_NAME}\b", re.IGNORECASE)
_USER_ID_RE = re.compile(r"^[A-Z0-9]{2,20}$")

logger = logging.getLogger(__name__)


class SandboxApp:
    """A Slack adapter connected to an in-memory workspace instead of Slack."""

    def __init__(self, adapter: SlackAppAdapter, *, workspace: SandboxWorkspace | None = None) -> None:
        self.adapter = adapter
        self.workspace = workspace or SandboxWorkspace()
        self.boot_id = uuid.uuid4().hex

    def post_message(self, *, user: str, text: str, thread_ts: str | None = None, wait: bool = False) -> str:
        """Post a user's message; reply as Slack Socket Mode would if it mentions the bot.

        "@athos" in the text becomes a real mention of the bot. Returns the
        message's ts. With wait, returns only after the bot has replied.
        """
        text = _MENTION_RE.sub(f"<@{BOT_USER_ID}>", text.strip())
        message = self.workspace.add_message(channel=CHANNEL_ID, text=text, user=user, thread_ts=thread_ts)
        event = {
            "type": "message",
            "channel_type": "channel",
            "channel": CHANNEL_ID,
            "user": user,
            "text": text,
            "ts": message.ts,
            **({"thread_ts": thread_ts} if thread_ts else {}),
        }
        if not should_reply(event, BOT_USER_ID):
            return message.ts
        reply_thread = thread_ts or message.ts
        question = clean_question(text, BOT_USER_ID)
        if not question:
            _post_response(
                self.workspace,
                channel=CHANNEL_ID,
                thread_ts=reply_thread,
                response=SlackMessageResponse(self.adapter.empty_prompt),
            )
            return message.ts
        request = SlackMessageRequest(
            CHANNEL_ID,
            reply_thread,
            message.ts,
            user,
            question,
            text,
            {"payload": {"event": event}, "event": event},
            partial(read_thread_history, self.workspace, BOT_USER_ID, CHANNEL_ID, reply_thread, message.ts),
        )
        self._run(_handle_message_request, request, wait=wait)
        return message.ts

    def click(self, *, user: str, message_ts: str, action_id: str, value: str | None, wait: bool = False) -> bool:
        """Press a button on a message, as a Slack block_actions payload."""
        message = self.workspace.get_message(message_ts)
        if message is None:
            return False
        slack_message = message.as_slack()
        payload = {
            "type": "block_actions",
            "user": {"id": user, "username": user.lower()},
            "channel": {"id": CHANNEL_ID, "name": CHANNEL_NAME},
            "container": {
                "type": "message",
                "message_ts": message_ts,
                "channel_id": CHANNEL_ID,
                **({"thread_ts": message.thread_ts} if message.thread_ts else {}),
            },
            "message": slack_message,
            "trigger_id": self.workspace.new_trigger(user),
            "actions": [{"action_id": action_id, "value": value, "type": "button"}],
        }
        self._run(_process_interaction, payload, wait=wait)
        return True

    def submit_view(self, *, user: str, values: dict[str, str], wait: bool = False) -> bool:
        """Submit the user's open modal; values map each input's action_id to its text."""
        view = self.workspace.take_view(user)
        if view is None:
            return False
        state: dict[str, dict[str, Any]] = {}
        for block in view.get("blocks") or []:
            action_id = (block.get("element") or {}).get("action_id")
            if block.get("type") == "input" and action_id:
                state[block.get("block_id") or action_id] = {
                    action_id: {"type": "plain_text_input", "value": values.get(action_id, "")}
                }
        payload = {
            "type": "view_submission",
            "user": {"id": user, "username": user.lower()},
            "view": {
                "callback_id": view.get("callback_id"),
                "private_metadata": view.get("private_metadata", ""),
                "state": {"values": state},
            },
        }
        self._run(_process_interaction, payload, wait=wait)
        return True

    def close_view(self, *, user: str) -> None:
        self.workspace.take_view(user)

    def state(self, user: str) -> dict[str, Any]:
        return {
            "boot_id": self.boot_id,
            "app_name": self.adapter.app_name,
            "bot": {"id": BOT_USER_ID, "name": BOT_NAME},
            "channel": {"id": CHANNEL_ID, "name": CHANNEL_NAME},
            **self.workspace.snapshot(user),
        }

    def _run(self, handler, request, *, wait: bool) -> None:
        # Production handles each event in its own daemon thread; so does the sandbox.
        worker = threading.Thread(target=handler, args=(self.adapter, self.workspace, request), daemon=True)
        worker.start()
        if wait:
            worker.join()


def _index_html() -> bytes:
    return resources.files(__package__).joinpath("static/index.html").read_bytes()


def _make_handler(app: SandboxApp) -> type[BaseHTTPRequestHandler]:
    page = _index_html()

    class Handler(BaseHTTPRequestHandler):
        server_version = "athos-slack-sandbox"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            logger.debug("%s - %s", self.address_string(), format % args)

        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            self._send(status, json.dumps(data).encode("utf-8"), "application/json")

        def _user(self, value: Any) -> str | None:
            user = str(value or DEFAULT_USER_ID).strip().upper()
            return user if _USER_ID_RE.match(user) else None

        def do_GET(self) -> None:  # noqa: N802 - stdlib name
            path, _, query = self.path.partition("?")
            if path in {"/", "/index.html"}:
                self._send(HTTPStatus.OK, page, "text/html; charset=utf-8")
            elif path == "/api/state":
                params = dict(part.split("=", 1) for part in query.split("&") if "=" in part)
                user = self._user(params.get("user"))
                if user is None:
                    self._json({"error": "invalid user id"}, HTTPStatus.BAD_REQUEST)
                else:
                    self._json(app.state(user))
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - stdlib name
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                self._json({"error": "invalid JSON"}, HTTPStatus.BAD_REQUEST)
                return
            user = self._user(body.get("user"))
            if user is None:
                self._json({"error": "user id must be 2-20 capital letters or digits"}, HTTPStatus.BAD_REQUEST)
                return
            if self.path == "/api/message":
                text = str(body.get("text") or "")
                if not text.strip():
                    self._json({"error": "empty message"}, HTTPStatus.BAD_REQUEST)
                    return
                ts = app.post_message(user=user, text=text, thread_ts=body.get("thread_ts") or None)
                self._json({"ok": True, "ts": ts})
            elif self.path == "/api/action":
                found = app.click(
                    user=user,
                    message_ts=str(body.get("message_ts") or ""),
                    action_id=str(body.get("action_id") or ""),
                    value=body.get("value"),
                )
                self._json({"ok": found}, HTTPStatus.OK if found else HTTPStatus.NOT_FOUND)
            elif self.path == "/api/view/submit":
                values = {str(k): str(v) for k, v in (body.get("values") or {}).items()}
                self._json({"ok": app.submit_view(user=user, values=values)})
            elif self.path == "/api/view/close":
                app.close_view(user=user)
                self._json({"ok": True})
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    return Handler


def make_server(app: SandboxApp, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """An HTTP server for the sandbox page; port 0 picks a free port."""
    server = ThreadingHTTPServer((host, port), _make_handler(app))
    server.daemon_threads = True
    return server


def serve(adapter: SlackAppAdapter, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the sandbox for `adapter` until interrupted."""
    server = make_server(SandboxApp(adapter), host, port)
    bound_host, bound_port = server.server_address[:2]
    print(f"{adapter.app_name} Slack sandbox at http://{bound_host}:{bound_port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

"""An in-memory Slack workspace standing in for slack_sdk's WebClient.

It implements the Web API calls the Slack runtime makes (auth_test,
chat_postMessage, chat_update, conversations_replies, reactions_add,
reactions_remove, views_open) with the same arguments and response shapes,
so the runtime's own code posts replies, reads threads and opens modals
against it unchanged. Everything lives in memory and is gone when the
process exits.
"""

from __future__ import annotations

import copy
import itertools
import threading
import time
from dataclasses import dataclass, field
from typing import Any

BOT_USER_ID = "UATHOSBOT"
BOT_ID = "BATHOSBOT"
BOT_NAME = "athos"
CHANNEL_ID = "CSANDBOX"
CHANNEL_NAME = "athos-sandbox"


@dataclass
class SandboxMessage:
    ts: str
    channel: str
    text: str
    user: str | None = None
    bot_id: str | None = None
    thread_ts: str | None = None
    blocks: list[dict[str, Any]] | None = None
    reactions: set[str] = field(default_factory=set)
    edited: bool = False

    def as_slack(self) -> dict[str, Any]:
        """The message as Slack's API returns it."""
        message: dict[str, Any] = {"type": "message", "ts": self.ts, "text": self.text}
        if self.user:
            message["user"] = self.user
        if self.bot_id:
            message["bot_id"] = self.bot_id
        if self.thread_ts:
            message["thread_ts"] = self.thread_ts
        if self.blocks:
            message["blocks"] = copy.deepcopy(self.blocks)
        return message


class SandboxWorkspace:
    """One channel's messages, threads, reactions and open modals."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: dict[str, SandboxMessage] = {}
        self._views: dict[str, dict[str, Any]] = {}
        self._trigger_users: dict[str, str] = {}
        self._clock = itertools.count()
        self._start = time.time()
        self.version = 0

    def next_ts(self) -> str:
        """A unique, increasing Slack-style timestamp."""
        return f"{self._start + next(self._clock) / 1000:.6f}"

    def _touch(self) -> None:
        self.version += 1

    # Slack Web API, as the runtime calls it.

    def auth_test(self) -> dict[str, Any]:
        return {"ok": True, "user_id": BOT_USER_ID, "user": BOT_NAME, "bot_id": BOT_ID}

    def chat_postMessage(
        self,
        *,
        channel: str,
        text: str,
        thread_ts: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        message = self.add_message(channel=channel, text=text, bot_id=BOT_ID, user=BOT_USER_ID, thread_ts=thread_ts, blocks=blocks)
        return {"ok": True, "channel": channel, "ts": message.ts, "message": message.as_slack()}

    def chat_update(
        self,
        *,
        channel: str,
        ts: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        with self._lock:
            message = self._messages.get(ts)
            if message is None or message.channel != channel:
                return {"ok": False, "error": "message_not_found"}
            message.text, message.blocks, message.edited = text, copy.deepcopy(blocks), True
            self._touch()
        return {"ok": True, "channel": channel, "ts": ts}

    def conversations_replies(self, *, channel: str, ts: str, cursor: str | None = None, **_: Any) -> dict[str, Any]:
        with self._lock:
            messages = [
                m.as_slack()
                for m in self._messages.values()
                if m.channel == channel and (m.ts == ts or m.thread_ts == ts)
            ]
        messages.sort(key=lambda m: float(m["ts"]))
        return {"ok": True, "messages": messages, "has_more": False, "response_metadata": {"next_cursor": ""}}

    def reactions_add(self, *, channel: str, name: str, timestamp: str, **_: Any) -> dict[str, Any]:
        return self._react(timestamp, name, add=True)

    def reactions_remove(self, *, channel: str, name: str, timestamp: str, **_: Any) -> dict[str, Any]:
        return self._react(timestamp, name, add=False)

    def views_open(self, *, trigger_id: str, view: dict[str, Any], **_: Any) -> dict[str, Any]:
        with self._lock:
            user = self._trigger_users.pop(trigger_id, None)
            if user is None:
                return {"ok": False, "error": "invalid_trigger_id"}
            self._views[user] = copy.deepcopy(view)
            self._touch()
        return {"ok": True, "view": view}

    # The sandbox UI's side.

    def add_message(
        self,
        *,
        channel: str,
        text: str,
        user: str | None = None,
        bot_id: str | None = None,
        thread_ts: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
    ) -> SandboxMessage:
        with self._lock:
            message = SandboxMessage(
                ts=self.next_ts(),
                channel=channel,
                text=text,
                user=user,
                bot_id=bot_id,
                thread_ts=thread_ts,
                blocks=copy.deepcopy(blocks),
            )
            self._messages[message.ts] = message
            self._touch()
            return message

    def get_message(self, ts: str) -> SandboxMessage | None:
        with self._lock:
            message = self._messages.get(ts)
            return copy.deepcopy(message) if message else None

    def new_trigger(self, user: str) -> str:
        with self._lock:
            trigger_id = f"trigger-{next(self._clock)}"
            self._trigger_users[trigger_id] = user
            return trigger_id

    def take_view(self, user: str) -> dict[str, Any] | None:
        with self._lock:
            view = self._views.pop(user, None)
            if view is not None:
                self._touch()
            return view

    def snapshot(self, user: str) -> dict[str, Any]:
        """The channel as the UI shows it: threads oldest first, each with its replies."""
        with self._lock:
            messages = sorted(self._messages.values(), key=lambda m: float(m.ts))
            view = copy.deepcopy(self._views.get(user))
            version = self.version
        threads: dict[str, dict[str, Any]] = {}
        for message in messages:
            entry = {**message.as_slack(), "reactions": sorted(message.reactions), "edited": message.edited}
            if message.thread_ts and message.thread_ts in threads:
                threads[message.thread_ts]["replies"].append(entry)
            else:
                threads[message.ts] = {"root": entry, "replies": []}
        return {"version": version, "threads": list(threads.values()), "view": view}

    def _react(self, timestamp: str, name: str, *, add: bool) -> dict[str, Any]:
        with self._lock:
            message = self._messages.get(timestamp)
            if message is None:
                return {"ok": False, "error": "message_not_found"}
            (message.reactions.add if add else message.reactions.discard)(name)
            self._touch()
        return {"ok": True}

"""SQLite-backed feedback storage for Slack responses."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Mapping


class FeedbackStore:
    """Persist Slack ratings and optional comments in a local SQLite database."""

    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS slack_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rating TEXT,
                kind TEXT NOT NULL,
                channel TEXT,
                message_ts TEXT,
                reactor_user_id TEXT,
                username TEXT,
                session_id TEXT,
                question TEXT,
                response_text TEXT,
                comment TEXT
            )
            """
        )
        self._connection.commit()

    def record(self, entry: Mapping[str, Any]) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO slack_feedback
                (timestamp, rating, kind, channel, message_ts, reactor_user_id,
                 username, session_id, question, response_text, comment)
                VALUES (:timestamp, :rating, :kind, :channel, :message_ts,
                 :reactor_user_id, :username, :session_id, :question,
                 :response_text, :comment)
                """,
                dict(entry),
            )
            self._connection.commit()

"""SQLite-backed feedback storage for Slack responses."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Mapping, Optional


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
        # One row per answered question, so a later "Take notes" click can see
        # the original answer and what the agent did to produce it.
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS slack_runs (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                user_id TEXT,
                question TEXT,
                answer TEXT,
                trace TEXT
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

    def save_run(self, entry: Mapping[str, Any]) -> None:
        """Insert one answered run (trace is a JSON string)."""
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO slack_runs
                (run_id, timestamp, session_id, user_id, question, answer, trace)
                VALUES (:run_id, :timestamp, :session_id, :user_id, :question,
                 :answer, :trace)
                """,
                {key: entry.get(key) for key in
                 ("run_id", "timestamp", "session_id", "user_id", "question", "answer", "trace")},
            )
            self._connection.commit()

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            cursor = self._connection.execute(
                "SELECT run_id, timestamp, session_id, user_id, question, answer, trace "
                "FROM slack_runs WHERE run_id = ?",
                (run_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(zip([column[0] for column in cursor.description], row))

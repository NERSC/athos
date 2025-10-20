"""Tests for the session store abstractions."""

import asyncio

import pytest

from athos.models.session import FlowSession
from athos.runtime.session_store import InMemorySessionStore, SessionStore


@pytest.mark.asyncio
async def test_get_or_create_creates_new_session() -> None:
    store: SessionStore = InMemorySessionStore()

    session = await store.get_or_create("session-1", "user-1", interface="cli")

    assert isinstance(session, FlowSession)
    assert session.session_id == "session-1"
    assert session.user_id == "user-1"
    assert session.interface == "cli"


@pytest.mark.asyncio
async def test_get_or_create_returns_existing_session() -> None:
    store = InMemorySessionStore()

    first = await store.get_or_create("session-1", "user-1")
    first.add_message("user", "hello")
    await store.save(first)

    second = await store.get_or_create("session-1", "user-1")

    assert second is first
    assert second.get_history() == [{"role": "user", "content": "hello"}]


@pytest.mark.asyncio
async def test_sessions_are_isolated_by_id() -> None:
    store = InMemorySessionStore()

    session_a = await store.get_or_create("session-1", "user-1")
    session_b = await store.get_or_create("session-2", "user-1")

    session_a.add_message("assistant", "A")
    session_b.add_message("assistant", "B")

    assert session_a.get_history() == [{"role": "assistant", "content": "A"}]
    assert session_b.get_history() == [{"role": "assistant", "content": "B"}]


@pytest.mark.asyncio
async def test_delete_removes_session() -> None:
    store = InMemorySessionStore()

    session = await store.get_or_create("session-1", "user-1")
    await store.save(session)

    await store.delete("session-1")

    new_session = await store.get_or_create("session-1", "user-1")
    assert new_session is not session
    assert new_session.get_history() == []


@pytest.mark.asyncio
async def test_list_sessions_filters_by_user() -> None:
    store = InMemorySessionStore()

    await store.get_or_create("session-1", "user-1")
    await store.get_or_create("session-2", "user-1")
    await store.get_or_create("session-3", "user-2")

    all_sessions = await store.list_sessions()
    user_1_sessions = await store.list_sessions("user-1")

    assert set(all_sessions) == {"session-1", "session-2", "session-3"}
    assert set(user_1_sessions) == {"session-1", "session-2"}


@pytest.mark.asyncio
async def test_get_or_create_is_atomic() -> None:
    store = InMemorySessionStore()

    async def worker() -> FlowSession:
        return await store.get_or_create("shared-session", "user-1")

    sessions = await asyncio.gather(*[worker() for _ in range(5)])

    first = sessions[0]
    for session in sessions[1:]:
        assert session is first

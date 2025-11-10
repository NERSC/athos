"""Utility helpers for ATHOS."""

from __future__ import annotations

from typing import Any

__all__ = [
    "get_workspace",
    "clear_workspace",
    "list_workspace_contents",
    "parse_overrides",
]


def get_workspace(*args: Any, **kwargs: Any):
    from .workspace import get_workspace as _get_workspace

    return _get_workspace(*args, **kwargs)


def clear_workspace(*args: Any, **kwargs: Any):
    from .workspace import clear_workspace as _clear_workspace

    return _clear_workspace(*args, **kwargs)


def list_workspace_contents(*args: Any, **kwargs: Any):
    from .workspace import list_workspace_contents as _list_workspace_contents

    return _list_workspace_contents(*args, **kwargs)


def parse_overrides(*args: Any, **kwargs: Any):
    from .config import parse_overrides as _parse_overrides

    return _parse_overrides(*args, **kwargs)


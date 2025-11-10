"""Path handling utilities for configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Union


def resolve_path(base_dir: Union[str, Path], relative_path_str: str) -> Path:
    """Resolve a possibly-relative path against a base directory.

    Args:
        base_dir: Base directory the configuration was loaded from.
        relative_path_str: Path string from the configuration (may be absolute).

    Returns:
        Absolute :class:`Path` pointing to the requested file.

    Raises:
        ValueError: If ``relative_path_str`` is empty.
    """
    if not relative_path_str:
        raise ValueError("Path value must be a non-empty string")

    relative_path = Path(relative_path_str)
    if relative_path.is_absolute():
        return relative_path

    return Path(base_dir) / relative_path


def read_text_file(file_path: Path) -> str:
    """Read text from ``file_path`` with standardized error handling."""
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found at '{file_path}'.")
    if not file_path.is_file():
        raise ValueError(f"Prompt path '{file_path}' is not a file.")

    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem errors are environment-specific
        raise OSError(f"Failed to read prompt file '{file_path}': {exc}") from exc

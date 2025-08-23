"""Utilities for managing a shared workspace directory."""

from pathlib import Path
import shutil
from typing import List

from athos.config import AthosConfig


def get_workspace(config: AthosConfig) -> Path:
    """Return the workspace path ensuring it exists."""
    path = Path(config.workspace_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_workspace(config: AthosConfig) -> None:
    """Remove all contents from the workspace directory."""
    path = get_workspace(config)
    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def list_workspace_contents(config: AthosConfig) -> List[Path]:
    """List contents of the workspace for debugging purposes."""
    path = get_workspace(config)
    return list(path.iterdir())


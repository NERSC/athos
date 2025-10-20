"""Enum definitions for ATHOS models."""

from enum import Enum


class ExecutionMode(str, Enum):
    """Supported execution modes for flows."""

    SYNC = "sync"
    STREAMING = "streaming"
    INTERACTIVE = "interactive"

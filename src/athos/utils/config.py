"""Configuration-related utility functions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict

import yaml


def parse_overrides(items: Iterable[str]) -> Dict[str, Any]:
    """Parse CLI-style override strings into a nested dictionary.

    Each item should be of the form ``path.to.key=value`` where ``value`` is
    parsed as YAML. The path segments are split on ``.`` and nested into a
    dictionary structure.

    Parameters
    ----------
    items:
        Iterable of override strings.

    Returns
    -------
    dict
        Nested dictionary representing the overrides.

    Raises
    ------
    ValueError
        If any item does not contain ``=`` to separate path and value.
    """

    overrides: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}', expected path=value")
        path, value_str = item.split("=", 1)
        value = yaml.safe_load(value_str)
        target = overrides
        parts = path.split(".")
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]  # type: ignore[assignment]
        target[parts[-1]] = value
    return overrides

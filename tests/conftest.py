"""Pytest configuration shared across all test suites."""

import pytest


def pytest_configure(config):
    """Register common markers to avoid unknown-marker warnings."""
    config.addinivalue_line("markers", "unit: fast, isolated tests")
    config.addinivalue_line("markers", "integration: cross-component or IO-oriented tests")
    config.addinivalue_line("markers", "slow: opt-in slow tests")


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test location."""
    from pathlib import Path

    unit_root = Path(config.rootpath) / "tests" / "unit"
    integration_root = Path(config.rootpath) / "tests" / "integration"

    for item in items:
        path = Path(item.fspath)
        if unit_root in path.parents:
            item.add_marker(pytest.mark.unit)
        elif integration_root in path.parents:
            item.add_marker(pytest.mark.integration)

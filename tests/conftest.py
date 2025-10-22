"""Pytest configuration and shared fixtures for ATHOS tests."""

import pytest


@pytest.fixture(autouse=True)
def isolate_flow_registry():
    """Isolate the flow registry between tests.

    This fixture automatically runs before and after each test to ensure
    that modifications to FLOW_REGISTRY don't leak between tests.

    The fixture:
    1. Saves the current registry state before the test
    2. Yields control to the test
    3. Restores the registry state after the test completes

    This allows tests to:
    - Clear the registry without affecting other tests
    - Register test flows without polluting other tests
    - Rely on real flows being registered (from module imports)
    """
    from athos.registry.flow_registry import FLOW_REGISTRY

    # Save current state
    saved_registry = FLOW_REGISTRY.copy()

    # Run the test
    yield

    # Restore state after test completes
    FLOW_REGISTRY.clear()
    FLOW_REGISTRY.update(saved_registry)

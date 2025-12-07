"""Unit test-specific configuration and fixtures."""

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def isolate_flow_registry():
    """Isolate the flow registry between unit tests.

    This ensures modifications to FLOW_REGISTRY do not leak across tests that
    register or clear flows during execution.
    """
    from athos.registry.flow_registry import FLOW_REGISTRY

    saved_registry = FLOW_REGISTRY.copy()
    try:
        yield
    finally:
        FLOW_REGISTRY.clear()
        FLOW_REGISTRY.update(saved_registry)

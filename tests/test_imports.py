def test_imports():
    try:
        import athos.agents
        import athos.core
        import athos.tools
    except ImportError as e:
        raise AssertionError(f"Failed to import ATHOS modules: {e}")

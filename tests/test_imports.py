def test_imports():
    try:
        import athos
        import athos.core
        import athos.tools
        import athos.flows
    except ImportError as e:
        raise AssertionError(f"Failed to import ATHOS modules: {e}")

def test_imports():
    try:
        import athos
        import athos.interfaces
        import athos.registry
        import athos.runtime
        import athos.tools
        import athos.frameworks
        import athos.frameworks.smolagents
    except ImportError as e:
        raise AssertionError(f"Failed to import ATHOS modules: {e}")

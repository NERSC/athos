"""
Pytest configuration for ATHOS tests.
This stubs out external dependencies so tests can run in isolation.
"""
import sys
import types

# Stub smolagents module
_smol = types.ModuleType('smolagents')
_smol.CodeAgent = type('CodeAgent', (), {})
_smol.OpenAIServerModel = type('OpenAIServerModel', (), {})
_smol.Tool = type('Tool', (), {})
sys.modules['smolagents'] = _smol

# Stub yaml module
_yaml = types.ModuleType('yaml')
_yaml.safe_load = lambda f: {}
sys.modules['yaml'] = _yaml
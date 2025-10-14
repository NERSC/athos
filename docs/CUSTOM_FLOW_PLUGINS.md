# Custom Flow Extensions

This document explains how to create and use custom flow extensions in ATHOS, allowing developers to extend the system with their own flow types by importing modules that register additional flows.

## Overview

ATHOS now supports dynamic flow registration through a runtime registry. This allows developers to:

1. Define custom flow types with their own configuration schemas
2. Implement custom execution logic
3. Register flows dynamically at runtime
4. Use custom flows alongside built-in flows

## Architecture Changes

### Before: Static Discriminated Union

Previously, flow types were defined using a static Pydantic discriminated union:

```python
FlowConfig = Annotated[
    Union[
        ChatbotFlowConfig,
        AgentFlowConfig,
    ],
    Field(discriminator='type')
]
```

This required all flow types to be known at compile time.

### After: Dynamic Registry-Based System

Now, flow types are registered dynamically in a registry:

```python
FLOW_REGISTRY: Dict[str, Tuple[Type[BaseFlowConfig], FlowFactory]] = {}
```

Configuration validation happens at runtime based on the registered flow types.

## Creating a Custom Flow Extension

### 1. Define Configuration Class

Create a configuration class that inherits from `BaseFlowConfig`:

```python
from typing_extensions import Literal
from pydantic import Field
from athos.config.models import BaseFlowConfig

class CustomFlowConfig(BaseFlowConfig):
    """Configuration for CustomFlow"""
    
    type: Literal["custom"]  # Unique flow type identifier
    custom_parameter: str = Field(description="A custom parameter")
    iterations: int = Field(default=3, gt=0, description="Number of iterations")
    enable_logging: bool = Field(default=True, description="Enable logging")
```

### 2. Implement Flow Class

Create a flow class that inherits from `BaseFlow`:

```python
from athos.core.flows import BaseFlow

class CustomFlow(BaseFlow):
    """Custom flow implementation"""
    
    def __init__(self, config: CustomFlowConfig, manager):
        self.config = config
        self.manager = manager
        self.model = manager._get_or_create_model(config.model)
        
    async def execute(self, input_data: str) -> Any:
        """Execute the custom flow"""
        # Your custom implementation here
        return {"result": "custom flow executed"}
```

### 3. Create Factory Function

Define a factory function to create flow instances:

```python
def create_custom_flow(cfg: CustomFlowConfig, manager) -> CustomFlow:
    """Factory function to create CustomFlow instances"""
    return CustomFlow(cfg, manager)
```

### 4. Register the Flow

Create a registration function:

```python
from athos.core.flow_registry import register_flow

def register_custom_flow():
    """Helper function to register the custom flow type"""
    register_flow("custom", CustomFlowConfig, create_custom_flow)
```

## Making the Flow Available

Ensure the module that registers your flow is imported before configuration loading:

```python
from my_package import flows  # noqa: F401 - triggers register_custom_flow()
```

## Configuration Usage

Once registered, custom flows can be used in YAML configuration:

```yaml
flows:
  my_custom_flow:
    type: "custom"  # Must match the registered type
    model: "gpt_4o"
    custom_parameter: "example_value"
    iterations: 3
    enable_logging: true
```

## Complete Example

See `examples/custom_flow_plugin.py` for a complete working example of module-based registration.

## Testing Your Extension

1. Create your flow extension following the structure above
2. Import it so the registration function runs
3. Create a configuration file that uses your custom flow type
4. Test with the provided test script:

```bash
python examples/test_dynamic_flows.py
```

## Best Practices

### Configuration Design

1. **Use descriptive field names** with clear documentation
2. **Provide sensible defaults** where possible
3. **Use Pydantic validators** for complex validation logic
4. **Inherit from BaseFlowConfig** to get common fields like `model`

### Flow Implementation

1. **Handle errors gracefully** and provide meaningful error messages
2. **Use the manager** to access models, tools, and MCP servers
3. **Follow async patterns** for consistency with other flows
4. **Log important events** for debugging and monitoring

### Registration

1. **Use unique type identifiers** to avoid conflicts
2. **Handle registration errors** gracefully
3. **Provide clear documentation** for your flow type
4. **Test with various configurations** to ensure robustness

## Migration Guide

### For Existing Code

Existing configurations will continue to work without changes. The new system is backward compatible.

### For New Extensions

Follow the patterns shown in this document to create new flow types that integrate seamlessly with the ATHOS ecosystem.

## Troubleshooting

### Common Issues

1. **"Unknown flow type" error**: Ensure your module is imported before configuration loading
2. **Validation errors**: Check that your config class matches the YAML structure
3. **Import errors**: Verify that your extension module is in the Python path

### Debugging

1. Enable debug logging to see flow registration messages
2. Use `get_available_flow_types()` to check registered flow types
3. Test configuration validation separately from execution

## API Reference

### Core Functions

- `register_flow(flow_type, config_cls, factory)`: Register a new flow type
- `get_available_flow_types()`: Get all registered flow types
- `is_flow_type_registered(flow_type)`: Check if a flow type is registered

### Base Classes

- `BaseFlowConfig`: Base class for flow configurations
- `BaseFlow`: Base class for flow implementations

### Registry

- `FLOW_REGISTRY`: Global registry of flow types
  - Register custom flows by importing the module that calls `register_flow()`

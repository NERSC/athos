# Dynamic Flow Plugin Implementation

This document summarizes the implementation of the dynamic registration approach for flow configuration in ATHOS. External
entry-point driven plugins have been removed in favour of registering flows directly within Python modules.

## Overview

The ATHOS system has been enhanced to support dynamic flow registration, replacing the previous static discriminated union
approach. This allows developers to create and register custom flow types at runtime by importing modules that invoke the
registry APIs.

## Key Changes Made

### 1. Configuration Model Changes (`src/athos/config/models.py`)

#### Before: Static Discriminated Union
```python
FlowConfig = Annotated[
    Union[
        ChatbotFlowConfig,
        AgentFlowConfig,
    ],
    Field(discriminator='type')
]
```

#### After: Dynamic Union with Runtime Validation
```python
# Dynamic FlowConfig - will be constructed at runtime based on registry
FlowConfig = Union[
    ChatbotFlowConfig,
    AgentFlowConfig,
]

class AthosConfig(BaseModel):
    flows: Dict[str, Union[FlowConfig, Dict[str, Any]]]
    
    @model_validator(mode='after')
    def validate_and_construct_flows(self):
        """Dynamically construct and validate flow configs based on registry"""
        # Ensure built-in flows are registered
        # Validate flow types against registry
        # Construct appropriate config objects
        # Validate cross-references
```

### 2. Enhanced Flow Registry (`src/athos/core/flow_registry.py`)

Added utility functions for better registry management:
- `get_available_flow_types()`: Get all registered flow types
- `is_flow_type_registered()`: Check if a flow type is registered

### 3. Manager Updates (`src/athos/core/manager.py`)

Updated flow creation to handle both enum and string flow types for backward compatibility:
```python
# Handle both enum and string types for backward compatibility
flow_type = flow_config.type.value if hasattr(flow_config.type, 'value') else flow_config.type
```

## Implementation Details

### Dynamic Validation Process

1. **Registration**: Built-in flows (and any additional modules) are imported so they can register themselves
2. **Type Discovery**: Flow type is extracted from configuration data
3. **Registry Lookup**: Appropriate config class is found in registry
4. **Dynamic Construction**: Config object is created using the registered class
5. **Cross-Reference Validation**: Models, tools, and MCP servers are validated

### Backward Compatibility

- Existing configurations continue to work without changes
- Built-in flow types (`chatbot`, `agent`) are automatically registered
- Enum-based type handling is preserved alongside string-based types

### Plugin Registration

Developers can register custom flows using direct registration:
```python
from athos.core.flow_registry import register_flow
register_flow("custom", CustomFlowConfig, create_custom_flow)
```

## Files Created/Modified

### Core Implementation
- `src/athos/config/models.py` - Dynamic validation logic
- `src/athos/core/flow_registry.py` - Enhanced registry functions
- `src/athos/core/manager.py` - Backward compatibility updates

### Examples and Documentation
- `examples/custom_flow_plugin.py` - Complete custom flow example
- `examples/config_with_custom_flow.yaml` - Configuration using custom flows
- `examples/test_dynamic_flows.py` - Test script demonstrating functionality
- `docs/CUSTOM_FLOW_PLUGINS.md` - Developer guide for creating custom flows
- `docs/DYNAMIC_FLOW_IMPLEMENTATION.md` - This implementation summary

## Testing Results

### Existing Tests
- ✅ All 66 config model tests pass
- ✅ All 28 config loader tests pass
- ✅ Backward compatibility maintained

### New Functionality
- ✅ Dynamic flow registration works
- ✅ Custom flow validation works
- ✅ Mixed built-in and custom flows work
- ✅ Error handling for unknown flow types

## Benefits Achieved

1. **Extensibility**: External packages can add new flow types
2. **Plugin Architecture**: Clean separation of core vs. extensions
3. **Runtime Discovery**: New flow types discovered at runtime
4. **Backward Compatibility**: Existing flows continue to work
5. **Type Safety**: Maintains validation through registered config classes
6. **Developer Experience**: Clear patterns for creating custom flows

## Usage Example

### Creating a Custom Flow
```python
class CustomFlowConfig(BaseFlowConfig):
    type: Literal["custom"]
    custom_parameter: str
    iterations: int = 3

class CustomFlow(BaseFlow):
    async def execute(self, input_data: str) -> Any:
        # Custom implementation
        return {"result": "custom flow executed"}

def register_custom_flow():
    register_flow("custom", CustomFlowConfig, create_custom_flow)
```

### Using in Configuration
```yaml
flows:
  my_custom_flow:
    type: "custom"
    model: "gpt_4o"
    custom_parameter: "example_value"
    iterations: 3
```

## Migration Path

For existing users:
- No changes required - existing configurations work as-is
- Additional flow types become available as soon as their modules are imported

For extension developers:
- Follow patterns in `examples/custom_flow_plugin.py`
- Ensure your package imports the registration helper at startup
- Inherit from `BaseFlowConfig` and `BaseFlow`

## Future Enhancements

Potential future improvements:
1. Automated module discovery for extension packages
2. Flow type versioning and compatibility checking
3. Dynamic schema generation for documentation
4. Extension dependency management
5. Hot-reloading of extensions during development

## Conclusion

The dynamic registration system successfully replaces the static discriminated union approach while maintaining full backward compatibility. External developers can now easily extend ATHOS with custom flow types without relying on packaging-time plugins.
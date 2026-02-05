# FlowSession State Serialization Requirements

## Summary

This document defines the rules for storing data in the `FlowSession.state` dictionary. To ensure that ATHOS sessions can be reliably persisted to backends like Redis or a database, all data stored in `FlowSession.state` **must be JSON-serializable**.

## The `state` Dictionary

The `FlowSession.state` field is a `Dict[str, Any]` designed as a flexible "scratchpad" for flows to store custom data that needs to persist between turns in a conversation.

While this offers great flexibility, it carries the risk of developers storing complex, non-serializable objects (e.g., file handles, database connections). While this works with the `InMemorySessionStore`, it will cause immediate failures when a persistent session store is implemented.

## Serialization Rules

To prevent future integration issues, the following rules must be adhered to by all flow implementations.

### ✅ Allowed Data Types

Only standard, JSON-serializable data types should be stored in `FlowSession.state`. These include:
- `str`
- `int`
- `float`
- `bool`
- `None`
- `list` or `tuple` (containing only other serializable types)
- `dict` (with `str` keys and serializable values)
- Pydantic `BaseModel` instances

### ❌ Forbidden Data Types

Do not store any object that cannot be easily serialized to and from JSON. This includes, but is not limited to:
- Open file handles (`_io.TextIOWrapper`)
- Database connections or clients
- Threading `Lock` objects or other synchronization primitives
- Instances of custom classes that are not Pydantic models

### Concrete Proposal for Documentation

To make these rules highly visible, they should be added directly to the docstring of the `FlowSession` class in `athos/src/athos/models/session.py`.

**Proposed Docstring:**
```python
class FlowSession(BaseModel):
    """
    Mutable session state maintained across flow executions.

    **Important Note on `state` Serialization:**

    The `state` dictionary is a flexible key-value store for custom flow data.
    To ensure that sessions can be reliably saved to persistent backends (like
    Redis or a database), all values stored in the `state` dictionary **MUST**
    be JSON-serializable.

    - ✅ **Allowed Types:** `str`, `int`, `float`, `bool`, `None`, `list`, `dict`.
      Pydantic models are also acceptable.
    - ❌ **Forbidden Types:** Do not store complex, non-serializable objects like
      file handles, database connections, or thread locks.

    **Example:**
    - GOOD: `session.state["last_record_id"] = 12345`
    - BAD:  `session.state["temp_file_handle"] = open("temp.txt", "w")`
    """
    # ... fields ...
    state: Dict[str, Any] = Field(default_factory=dict)
    # ...
```

Adhering to these guidelines is crucial for the long-term stability and scalability of the ATHOS platform.

# Future Development Guide

This guide outlines the architectural vision for the Athos project, providing a roadmap for future development. It is based on the package structure separating core logic into `interfaces`, `runtime`, and `registry` packages. Adhering to this structure will help keep the codebase clean, scalable, and maintainable.

## 1. Architectural Principles

*   **Separation of Concerns**: Each package should have a single, well-defined responsibility.
*   **Dependency Inversion**: High-level modules should not depend on low-level modules; both should depend on abstractions. Our `interfaces` package provides these abstractions.
*   **Decoupling**: Core application logic should remain independent of its delivery mechanism (e.g., Web API, CLI).

## 2. The `runtime` Package: The Application's Engine

The `athos.runtime` package is the heart of the application. It is responsible for the orchestration, execution, and lifecycle management of all core components. It should remain framework-agnostic (i.e., no web server or CLI-specific code).

### Future Modules for the `runtime` Package

As the application grows, we envision the `runtime` package expanding with the following modules:

#### `runtime.builder` (Existing)
*   **Responsibility**: Constructing and initializing components based on the application configuration.
*   **Current functions**: `build_config`, `build_flow`.

#### `runtime.runner`
*   **Responsibility**: Executing flows and managing their lifecycle.
*   **Potential features**:
    *   A `run()` function that takes a flow object and input data.
    *   Centralized `try...finally` logic to ensure `flow.close()` is always called.
    *   Robust error handling and logging for flow execution.
    *   Management of the `asyncio` event loop for concurrent flow execution.

#### `runtime.context`
*   **Responsibility**: Managing shared, request-scoped state.
*   **Potential features**:
    *   A `RuntimeContext` data class to hold information like user IDs, session data, or request tracers.
    *   The context would be created by the `runner` and passed to the executing flow, providing a clean way to access shared state.

#### `runtime.hooks`
*   **Responsibility**: Providing a middleware or plugin system for extensibility.
*   **Potential features**:
    *   A `HookManager` to register custom functions that run at specific points in the lifecycle (e.g., `on_flow_start`, `on_flow_error`).
    *   The `runner` would trigger these hooks, allowing for cross-cutting concerns like metrics, caching, or custom logging without altering core flow logic.

#### `runtime.resources`
*   **Responsibility**: Managing the lifecycle of shared, expensive resources.
*   **Potential features**:
    *   Initializing and holding pools for database connections, persistent HTTP clients, etc.
    *   Providing a clean interface for flows to access these resources, likely via the `RuntimeContext`.

## 3. The `server` Package: The Web API Layer

To expose Athos agents via a web API (e.g., using FastAPI), a dedicated `athos.server` package should be created. This package acts as a translation layer, converting HTTP requests into calls to the `runtime` engine.

**Crucially, the `runtime` package should never import from the `server` package.**

### Proposed `server` Package Structure

```
src/athos/
└── server/
    ├── __init__.py
    ├── main.py         # FastAPI app instance, startup/shutdown events
    ├── dependencies.py # Shared dependencies (e.g., getting config)
    └── endpoints/
        ├── __init__.py
        └── flows.py    # API routes for executing flows
```

### How It Works

1.  **`server.main`**: This is the entry point for the web server (e.g., for `uvicorn`). It should use the `runtime.builder` during the `startup` event to load the application configuration once.
2.  **`server.endpoints`**: These modules define the API routes (e.g., `POST /flows/{flow_name}/execute`).
3.  **Route Handlers**: The functions handling API requests are clients of the `runtime` package. They should:
    a. Parse and validate the incoming HTTP request.
    b. Call functions from `athos.runtime.builder` and `athos.runtime.runner` to execute the requested flow.
    c. Format the result from the runtime into an HTTP response.

By keeping the `server` and `runtime` concerns separate, we ensure the core logic of Athos remains reusable and independent, allowing for multiple ways to interact with it (API, CLI, etc.) without code duplication.

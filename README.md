# nersc-athos

ATHOS: Agentic Toolkit for HPC Operations Support

## Package Structure

This monorepo contains three main packages that work together to provide agentic AI support for HPC operations:

### `athos-core/`
**Core abstractions for ATHOS**

The foundational package containing the core abstractions, interfaces, and base classes that define the ATHOS framework. This package provides the essential building blocks that other ATHOS packages depend on.

- **Purpose**: Core framework definitions and abstractions
- **Dependencies**: Python >=3.8 (no external dependencies)
- **Package**: `athos.core`

### `athos-tools/`
**Tools and utilities for ATHOS agents**

A collection of tools, utilities, and helper functions designed to support ATHOS agents in their HPC operations. This package provides the practical implementations and utilities that agents use to interact with HPC systems.

- **Purpose**: Utility functions and tools for agent operations
- **Dependencies**: Python >=3.8 (no external dependencies)
- **Package**: `athos.tools`

### `athos-agents/`
**Predefined agents for HPC support using ATHOS**

Contains pre-built, specialized agents designed for specific HPC support tasks. These agents leverage the core abstractions and tools to provide ready-to-use solutions for common HPC operational scenarios.

- **Purpose**: Ready-to-use agents for HPC support tasks
- **Dependencies**: `athos-core`, `athos-tools`
- **Package**: `athos.agents`

## Development Setup

The project uses Poetry for dependency management with local path dependencies to enable seamless development across all packages. All packages are configured with `develop = true` to allow for live editing during development.

```bash
# Install all packages and dependencies
poetry install

# Run tests
poetry run pytest
```

## Architecture

The packages follow a layered architecture:
- **athos-core**: Foundation layer with core abstractions
- **athos-tools**: Utility layer with practical implementations
- **athos-agents**: Application layer with specialized agents

This structure allows for modular development while maintaining clear separation of concerns across the different aspects of the ATHOS framework.

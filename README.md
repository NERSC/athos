# nersc-athos

ATHOS: Agentic Toolkit for HPC Operations Support

## Dev setup

Local development:

```bash
pip install -e .[dev]
```

On NERSC systems, simply run the provided setup script:

```bash
./scripts/create_env_nersc.sh
```

## Running the command line interface

On NERSC you must first load Conda and activate the ATHOS environment in each session:

```bash
ml conda
conda activate athos
```

From the top level folder, you can then run the CLI:

```bash
python -m athos.main --config config/config.yaml --flow hpc_chatbot --input "what is NERSC?"
```

## Package Structure

The project is structured as a single Python package `athos` with the following modules:

### `src/athos/core/`
**Core framework and management layer**

Contains the foundational components for managing and orchestrating ATHOS agents and tools:

- **`manager.py`**: Defines the `AthosManager` class that handles configuration, and initialization of models, flows, tools.
- **`flows.py`**: Execution flow implementations including `CodeAgentFlow` and `ChatbotFlow` 
- **`agent.py`** and **`tool.py`**: Deprecated base classes (being phased out)

### `src/athos/agents/`
**Agent implementations**

Contains concrete agent implementations:

- **`openai_agent.py`**: Deprecated OpenAI-based agent classes

### `src/athos/tools/`
**HPC-specific tools and utilities**

Custom tools designed for HPC operations:

- **`slurm_query.py`**: Utility for querying SLURM jobs
- **`slurm_mcp/`**: MCP server providing secure SLURM command execution
- **`servicenow-mcp/`**: Tools for interacting with ServiceNow from HPC workflows

### `src/athos/examples/`
**Usage examples and demonstrations**

- **`basic_usage.py`**: *Untested* example implementations showing how to use ATHOS agents and flows

### `src/athos/main.py`
**CLI interface and entry point**

Main command-line interface for running ATHOS agents with configuration-driven execution.

### `evals/`
**Test cases and evaluation pipeline**

Synthetic use cases to evaluate performance of agent configurations.
See [evals/README.md](evals/README.md) for instructions on how to run.

## Key Architecture Notes

- The project uses a **configuration-driven approach** where agents, tools, and execution flows are defined in YAML configuration files
- **Dynamic tool loading** allows tools to be loaded at runtime based on configuration
- **Multiple execution flow types** are supported (chatbot, code agent, prompt chains)
- The framework is built on top of the **OpenAI Agents SDK** and **Hugging Face SmolAgents**

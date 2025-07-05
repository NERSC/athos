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

You can override the configured logging verbosity for a single run using
`--log-level`:

```bash
python -m athos.main --config config/config.yaml --flow hpc_chatbot --input "what is NERSC?" --log-level DEBUG
```

### Logging

Logging behavior is controlled through the optional `logging_config` section in
your YAML configuration. Simple dictionaries with `level` and `format` keys are
passed through to `logging.basicConfig`. If you provide a `version` key, the
dictionary is treated as a full `logging.config.dictConfig` specification.
For convenience a lightweight schema is also supported:

```yaml
logging_config:
  level: INFO
  format: "%(asctime)s %(levelname)s %(message)s"
  handlers:
    - type: console
    - type: file
      filename: /tmp/athos.log
```

When `handlers` are present the helper converts the dictionary into a `dictConfig`
and configures the root logger accordingly. If a file handler specifies a path
whose parent directory doesn't exist, it will be created automatically.

## Package Structure

The project is structured as a single Python package `athos` with the following modules:

### `src/athos/core/`
**Core framework and management layer**

Contains the foundational components for managing and orchestrating ATHOS agents and tools:

- **`manager.py`**: Defines the `AthosManager` class that handles configuration, and initialization of models, flows, tools.
- **`flows.py`**: Execution flow implementations including `AgentFlow` and `ChatbotFlow`
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
- **`servicenow_mcp/`**: Tools for interacting with ServiceNow from HPC workflows

### `src/athos/examples/`
**Usage examples and demonstrations**

Example scripts demonstrating agent and tool integrations can be found in this
directory. For instance `filesystem_agent.py` showcases the MCP filesystem
tools.

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

### Tool Plugins

Third-party packages can provide additional tools via the `athos_tools` entry point.
Each plugin should expose a callable that registers tools using
`athos.core.tool_registry.register_tool`. Example `pyproject.toml` snippet:

```toml
[project.entry-points.athos_tools]
my_plugin = "my_package.tools:register"
```

Where `my_package.tools.register` invokes `register_tool` with a tool factory.

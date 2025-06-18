# SLURM MCP Server

A Model Context Protocol (MCP) server for executing common SLURM commands with safety checks.

## Features

- Secure execution of multiple SLURM commands:
  - `sacct`: Account information for jobs
  - `showquota`: Display quota information  
  - `sinfo`: Information about SLURM nodes and partitions
- Input validation and security checks
- Async/await support
- Comprehensive error handling
- Command-specific argument validation

## Setup

This project uses `uv` for dependency management. To set up:

1. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the server:
   ```bash
   uv run python slurm_mcp_server.py
   ```

## Usage

The server provides three tools, each accepting an array of arguments to pass to the respective SLURM command.

### Available Commands

#### sacct - Account Information
Get information about jobs and job steps.

```python
# Get help
sacct --help

# Get recent jobs
sacct -S today

# Get detailed job information
sacct -S today --format=JobID,JobName,State,ExitCode,Start,End

# Get jobs for a specific user
sacct -u username -S today

# Get jobs in a specific state
sacct -S today --state=COMPLETED
```

#### showquota - Quota Information
Display quota information for the current user.

```python
# Get quota information for current user
showquota

# Note: showquota does not accept any parameters
```

#### sinfo - System Information
Get information about SLURM nodes and partitions.

```python
# Get help
sinfo --help

# Show all nodes
sinfo -N

# Show partition information
sinfo -s

# Show detailed node information
sinfo -N --format=NodeList,State,CPUs,Memory,AllocMem,FreeMem

# Show nodes in specific partition
sinfo -p partition_name

# Show nodes by state
sinfo -t idle,alloc,down
```

## Security

The server includes several security measures:
- Input validation to prevent command injection
- Restricted character set for arguments
- Command-specific validation rules
- Safe execution environment
- Whitelist of allowed commands

## Development

To run tests:
```bash
uv run pytest
```

## Migration from sacct.py

If you were using the previous `sacct.py` server, you can now use the new `slurm_mcp_server.py` which provides the same `sacct` functionality plus additional commands. The API remains the same for the `sacct` tool. 
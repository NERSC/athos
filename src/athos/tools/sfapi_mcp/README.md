# NERSC SuperFacility API MCP Server

This Model Context Protocol (MCP) server provides access to NERSC's SuperFacility API, allowing you to interact with NERSC computing resources through MCP-compatible clients, e.g. in agentic AI workflows.

## Features

- **System Status**: Check the status of NERSC systems (no authentication required)
- **File Operations**: List directories and get file information
- **Job Management**: Submit jobs, check job status, and monitor job queues
- **Command Execution**: Run commands on login nodes
- **Resource Monitoring**: Check compute allocations and usage
- **File Transfer**: Transfer files between NERSC systems
- **Outage Information**: Get planned maintenance and outage information

## Configuration

1. Create a SuperFacility API client in [NERSC Iris](https://iris.nersc.gov/profile)
2. Download your private key
3. Provide credentials via environment variables or command line options.
   Environment variables can be placed in a `./.env` file:

```
NERSC_CLIENT_ID=your_client_id_here
NERSC_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
```

## Usage

### Running the Server

```bash
python nersc_mcp/server.py --client-id $NERSC_CLIENT_ID --private-key-path $NERSC_PRIVATE_KEY_PATH
```

Or if installed:
```bash
nersc-sfapi-mcp --client-id $NERSC_CLIENT_ID --private-key-path $NERSC_PRIVATE_KEY_PATH
```

## Available Tools

### System Information (No Authentication Required)
- `get_system_status`: Get status of NERSC systems
- `get_system_info`: Get detailed system information
- `get_outages`: Get planned outages and maintenance

### File Operations (Authentication Required)
- `list_directory`: List directory contents
- `get_file_info`: Get file information
- `transfer_file`: Transfer files between systems

### Job Management (Authentication Required)
- `submit_job`: Submit batch jobs
- `get_job_queue`: Check job queue status
- `get_task_status`: Get task execution results

### Command Execution (Elevated Authentication Required)
- `run_command`: Execute commands on login nodes

### Account Management (Authentication Required)
- `get_compute_allocation`: Check compute allocation usage

## Authentication

The server uses OAuth2 client credentials flow. You need to:

1. Create a SuperFacility API client in NERSC Iris
2. Choose appropriate security level based on your needs:
   - **Level 1**: Basic operations (60-day lifetime)
   - **Level 2**: Elevated operations (30-day lifetime)
   - **Level 3**: Administrative operations (2-day lifetime)

3. Download the private key and configure the server

## Security Considerations

- Store private keys securely and never commit them to version control
- Use environment variables for sensitive configuration
- Choose the minimum security level needed for your use case
- Regularly rotate your API clients

## Common NERSC Systems

- `perlmutter`: Primary compute system
- `cori`: Legacy compute system (being retired)
- `dtn`: Data transfer nodes
- `archive`: HPSS archive system

## Example Usage

```python
# Check system status (no auth required)
status = await get_system_status("perlmutter")

# List home directory (auth required)
files = await list_directory("perlmutter", "/global/homes/u/username")

# Submit a job (auth required)
result = await submit_job("perlmutter", "/global/homes/u/username/job.slurm")

# Check job status
task_status = await get_task_status(result["task_id"])
```

## Error Handling

The server provides comprehensive error handling:
- Authentication errors are clearly reported
- Network timeouts are handled gracefully
- API rate limits are respected
- Invalid parameters are validated

## References

- [NERSC SuperFacility API Documentation](https://docs.nersc.gov/services/sfapi/)
- [NERSC SuperFacility API Examples](https://docs.nersc.gov/services/sfapi/examples/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

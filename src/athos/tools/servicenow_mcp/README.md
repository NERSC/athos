# ServiceNow MCP Tools

This module provides Model Context Protocol tools for interacting with
ServiceNow. Attachments downloaded via the `download_attachment` tool are
written to the shared workspace directory. Set the `ATHOS_WORKSPACE`
environment variable (or `workspace_dir` in `config/config.yaml`) to control
where files are stored. If unset, `/tmp/athos_workspace/attachments` is used.


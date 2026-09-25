# ServiceNow MCP Tools

This module provides Model Context Protocol tools for interacting with
ServiceNow. Attachments downloaded via the `download_attachment` tool are
written to the shared workspace directory. Set the `ATHOS_WORKSPACE`
environment variable (or `workspace_dir` in `config/config.yaml`) to control
where files are stored. If unset, `/tmp/athos_workspace/attachments` is used.

## Incident filtering

`list_incidents` uses structured filters for incident fields and returns
newest-created incidents by default. Its `query` argument is only a plain-text
search across `short_description` and `description`; it does not accept encoded
ServiceNow queries or field expressions.

Resolve a human-readable assignment-group name before filtering incidents:

1. Call `list_groups(query="DAS")` and select an unambiguous group.
2. Pass that group's `sys_id` to
   `list_incidents(assignment_group="...", active=true)`.

Both tools return their applied filters and ordering in the response so callers
can verify that the requested query was executed.

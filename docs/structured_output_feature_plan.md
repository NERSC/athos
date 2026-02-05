# Development Plan: Dynamic Structured Output in Prompt Chaining Flow

## 1. Overview

This document outlines the plan for a follow-up enhancement to the "General-Purpose Prompt Chaining Flow." The goal is to add support for dynamically requesting structured output (e.g., JSON) from language models, with the desired schema being defined directly within the YAML flow configuration.

This feature will allow individual steps in a `langgraph_chain` flow to reliably extract information into a predictable, machine-readable format.

## 2. Proposed Configuration Change

To implement this, we will introduce a new optional field, `output_schema`, to the `steps` configuration.

### Schema Enhancement:

*   `output_schema` (dict, optional): A dictionary representing the JSON Schema for the desired output. If a step includes this field, the flow will instruct the model to return a JSON object conforming to this schema.

### Example:

This example demonstrates a step that extracts specific fields from a raw text block into a structured object.

```yaml
- name: extract_structured_data
  prompt: >
    From the following incident details, extract the key metadata as a JSON object.

    Incident Details:
    {incident_details_raw}
  tools: []
  output_key: structured_ticket
  output_schema:
    title: IncidentMetadata
    description: Structured metadata from a ServiceNow incident.
    type: object
    properties:
      incident_number:
        type: string
        description: The unique identifier for the incident (e.g., INC12345).
      short_description:
        type: string
        description: A brief summary of the incident.
      priority:
        type: integer
        description: The priority level of the ticket (e.g., 1, 2, 3).
      state:
        type: string
        description: The current state of the incident (e.g., 'New', 'In Progress').
    required: ["incident_number", "short_description", "priority", "state"]
```

## 3. Implementation Steps

### Step 1: Update Configuration Models

In `src/athos/config/models.py`, update the `LangGraphChainStep` Pydantic model to include the new optional field.

```python
# In class LangGraphChainStep
...
output_schema: Optional[dict] = None
```

### Step 2: Enhance the Node Execution Logic

In `src/athos/frameworks/langgraph/chain_flow.py`, modify the `execute_step` function within the `LangGraphChainFlow` class.

The logic should be updated as follows:
1.  Inside the function, check if `step_config.output_schema` is present.
2.  If it is, get the base LLM and bind it to the schema using the `.with_structured_output()` method:
    ```python
    model = get_base_model() # Or however the model is provisioned
    structured_model = model.with_structured_output(step_config.output_schema)
    # The agent/executor for this step must use `structured_model`
    ```
3.  If `output_schema` is not present, the function should proceed with the existing logic, using the standard model without a structured output binding.

### Step 3: Update Testing

In the test file for the `langgraph_chain` flow (e.g., `tests/frameworks/langgraph/test_chain_flow.py`), add a new test case specifically for this feature.

*   Create a test that runs a `langgraph_chain` flow containing a step with an `output_schema`.
*   The test should assert that the output of this step, as stored in the final state dictionary, is a dictionary (or a Pydantic object) that correctly matches the structure defined in the `output_schema`.
*   The test should also confirm that steps *without* the schema still produce regular string outputs.

## 4. Complete Example Use Case

This updated workflow demonstrates how the raw output from one step (`incident_details_raw`) is transformed into structured data (`structured_ticket`) in the next, which is then used by subsequent steps.

```yaml
# In config/config.yaml under the 'flows' section

- name: servicenow_ticket_ingestion_structured
  type: langgraph_chain
  steps:
    - name: retrieve_ticket
      prompt: "Use tools to get the incident with the number: {incident_number}."
      tools: [servicenow_mcp]
      output_key: incident_details_raw

    - name: extract_structured_data
      prompt: "From the following incident details, extract the key metadata."
      tools: []
      output_key: structured_ticket
      output_schema:
        title: IncidentMetadata
        description: "Structured metadata from a ServiceNow incident."
        type: object
        properties:
          incident_number: { type: "string" }
          short_description: { type: "string" }
          priority: { type: "integer" }
          state: { type: "string" }
        required: ["incident_number", "short_description", "priority", "state"]

    - name: format_summary
      prompt: >
        Using the following structured data, write a concise, human-readable summary
        for a status report.

        Data:
        {structured_ticket}
      tools: []
      output_key: incident_summary

    - name: save_summary_to_file
      prompt: "Save the following summary to a file named '{structured_ticket[incident_number]}.txt'."
      tools: [filesystem_mcp]
      output_key: file_save_status
```

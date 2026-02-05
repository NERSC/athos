# Development Plan: General-Purpose Prompt Chaining Flow

## 1. Overview

This document outlines the development plan for creating a new, general-purpose prompt chaining flow within the ATHOS framework. This flow will be built using `langgraph` and will be fully configurable via YAML, allowing users to define complex, multi-step workflows without writing new Python code.

The core principle is to create a `flow` type that can dynamically construct and execute a graph of interconnected LLM calls based on a list of "steps" defined in the configuration.

## 2. Key Features

*   **Configuration-Driven:** The entire workflow (sequence of steps, prompts, tools) will be defined in `config.yaml`.
*   **Flexible State Management:** The flow will use a simple `dict` for state, allowing data to be passed between steps dynamically using named keys.
*   **Per-Step Tools:** The configuration will allow for specifying a unique set of tools for each step in the chain, ensuring the agent only has access to the tools it needs for the current task.
*   **Sequential Execution:** The initial version will focus on linear, sequential execution of steps, where the output of one step is available to the next.

## 3. Configuration Design

A new `type` of flow, `langgraph_chain`, will be introduced. The configuration will be a list of `steps`, where each step is an object with a `name`, `prompt`, `tools`, and an `output_key`.

### Schema:

*   `type: langgraph_chain`: The identifier for this new flow.
*   `steps`: A list of step configurations.
    *   `name` (str): A unique name for the step.
    *   `prompt` (str): The prompt template for the step. It can contain placeholders for keys from the state dictionary (e.g., `{input_key}`).
    *   `tools` (list[str]): A list of tool names to be made available to the agent for this step.
    *   `output_key` (str): The key under which the step's output will be saved in the state dictionary.

## 4. Implementation Steps

### Step 1: Define Configuration Models

In `src/athos/config/models.py`, define new Pydantic models to parse and validate the `langgraph_chain` flow configuration from the YAML file.

*   `LangGraphChainStep`: A model for a single step (`name`, `prompt`, `tools`, `output_key`).
*   `LangGraphChainFlowConfig`: The main model for the flow (`name`, `type`, `steps`).

### Step 2: Create the Flow Class

Create a new file, `src/athos/frameworks/langgraph/chain_flow.py`, to house the new flow implementation.

*   Define a class `LangGraphChainFlow` that inherits from `BaseFlow`.
*   This class will take the `LangGraphChainFlowConfig` as input.
*   Register this new flow type in the `FlowRegistry` (`src/athos/registry/flow_registry.py`) with the key `langgraph_chain`.

### Step 3: Implement Graph Construction

Inside `LangGraphChainFlow`, implement the logic to build the `langgraph.StateGraph`.

*   The `__init__` or a `setup()` method should dynamically construct the graph.
*   Initialize `StateGraph` with `dict` as the state schema: `graph = StateGraph(dict)`.
*   Define a generic node function, e.g., `execute_step(state: dict, step_config: LangGraphChainStep)`. This function will be the execution engine for every step.
*   Iterate through the `steps` in the configuration:
    *   Add a node for each step using `graph.add_node()`. Use a `functools.partial` to pass the specific `step_config` to the generic `execute_step` function.
    *   Set the entry point to the first step.
    *   Add edges to connect the steps in a linear sequence.
*   Compile the graph using `graph.compile()`.

### Step 4: Implement the Node Execution Logic

The `execute_step` function is the core of the runtime execution. It should:
1.  Accept the current `state` dictionary and the `step_config` for its specific step.
2.  Load the tools specified in `step_config.tools`. (This will require using ATHOS's existing tool loading/factory mechanisms).
3.  Create an agent/executor for the step, providing it with the LLM and the loaded tools.
4.  Format the prompt from `step_config.prompt` using the `state` dictionary: `formatted_prompt = prompt.format(**state)`.
5.  Invoke the agent with the `formatted_prompt`.
6.  Return the result in a dictionary with the configured `output_key`: `return {step_config.output_key: result}`.

### Step 5: Implement Testing

Create a new test file in `tests/frameworks/langgraph/` to validate the new flow.

*   **Unit Test:** Write a test to ensure the `LangGraphChainFlow` correctly builds a graph from a sample configuration.
*   **Integration Test:** Create a complete integration test that uses the "ServiceNow Ticket Ingestion" configuration (see below). This test will run the full flow end-to-end, mocking any external services if necessary, and verify the final output.

## 5. Example Use Case: ServiceNow Ticket Ingestion

This configuration will be added to `config/config.yaml` to drive the integration test and serve as the primary example. The flow takes an `incident_number` as its initial input.

```yaml
# In config/config.yaml under the 'flows' section

- name: servicenow_ticket_ingestion
  type: langgraph_chain
  steps:
    - name: retrieve_ticket
      prompt: >
        You are an IT support specialist. Your task is to retrieve details for a specific ServiceNow incident.
        Use the available tools to get the incident with the number: {incident_number}.
      tools:
        - servicenow_mcp
      output_key: incident_details

    - name: summarize_incident
      prompt: >
        You are a technical writer. Based on the following incident details, write a concise,
        well-formatted summary for a status report. Include the incident number, short description,
        state, and business impact.

        Incident Details:
        {incident_details}
      tools: []
      output_key: incident_summary

    - name: save_summary_to_file
      prompt: >
        You are a file system assistant. Your task is to save the provided text content to a local file.
        Use the available tools to write the following summary to a file named '{incident_number}.txt'.

        Content to Save:
        {incident_summary}
      tools:
        - filesystem_mcp
      output_key: file_save_status
```

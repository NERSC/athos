Task: Refactor and Standardize Prompt Configuration Across All Flows

Objective: Improve the clarity, maintainability, and consistency of prompt configuration by adopting
framework-idiomatic field names (system_prompt vs. instructions) and implementing a robust,
Pydantic-native mechanism for loading prompt content from files.

Description:

The current system has a centralized and inconsistent approach to loading prompts. This task is to
refactor this by removing the centralized logic from ConfigLoader and implementing Pydantic-native
validation and file-loading within each relevant flow configuration class. A clear convention for prompt
field names (system_prompt vs. instructions) will be established based on the underlying framework's
behavior.

Implementation Steps:

 1. Create Utility Functions (`src/athos/utils/paths.py`):
     * Implement resolve_path(base_dir: Union[str, Path], relative_path_str: str) -> Path: Resolves a path
       string relative to a base directory, also handling absolute paths.
     * Implement read_text_file(file_path: Path) -> str: Reads the content of a text file with standardized
        error handling.

 2. Update `ConfigLoader` (`src/athos/config/__init__.py`):
     * Remove the _resolve_prompt_paths method entirely.
     * Modify ConfigLoader.load_config to pass config_path.parent into the Pydantic validation context as
       {"config_dir": config_path.parent}.

 3. Update Flow Configurations and Conventions:
     * Establish Convention:
         * `system_prompt` / `system_prompt_path`: Use for flows that define the entire system prompt. This
            applies to all chatbot and langgraph based agent flows.
         * `instructions` / `instructions_path`: Use for flows that append instructions to a base prompt,
           such as the smol-agents AgentFlow.
     * Implement in Pydantic Models:
         * For each relevant flow config class (e.g., LangChainAgentFlowConfig, AgentFlowConfig,
           ChatbotFlowConfig), ensure the appropriate _path field exists (e.g., add system_prompt_path to
           LangChainAgentFlowConfig, add instructions_path to AgentFlowConfig).
         * Implement a model_validator(mode="before") in each of these classes. The validator must use the
           new utility functions (resolve_path, read_text_file) to load content from the _path variant into
            the main content field (e.g., system_prompt_path -> system_prompt).
         * The validator must also check for ambiguity (e.g., both system_prompt and system_prompt_path
           being defined) and raise a ValueError.

 4. Update Flow `create` Methods:
     * Ensure the create classmethod in each updated flow correctly uses the resolved prompt field
       (system_prompt or instructions).

 5. Update `config.yaml`:
     * Modify all flow definitions in config/config.yaml to use the new, consistent field names (e.g.,
       system_prompt_path for langchain_web_agent, instructions_path for hpc_consultant).

Acceptance Criteria:

 * The ConfigLoader is simplified and contains no flow-specific prompt logic.
 * langchain_agent and chatbot flows successfully load prompts using system_prompt or
   system_prompt_path.
 * The hpc_consultant (smol-agent) flow successfully loads its instructions using instructions or
   instructions_path.
 * Providing both an inline prompt and a path for the same flow (e.g., system_prompt and
   system_prompt_path) results in a validation error.
 * All project tests pass after the refactoring.

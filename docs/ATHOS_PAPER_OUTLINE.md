# ATHOS: Agentic Toolkit for HPC Operations Support

## Abstract
High-performance computing (HPC) centers are becoming harder to operate as
architectures diversify, workflows grow in scale, and user expectations rise.
This paper presents **ATHOS**, a lightweight yet flexible toolkit that equips
agents with the tools, models, and orchestration logic needed to assist with
HPC operations and user support. ATHOS builds on modern language models and a
registry-based architecture to interface with services such as ServiceNow,
SLURM, and the Superfacility API. We outline the design of the toolkit,
describe an evaluation framework for benchmarking agentic workflows, and
highlight ongoing deployment and testing at NERSC. Results and detailed
workflows are forthcoming as the system matures.

## 1. Introduction
Scientific computing facilities underpin discovery across physics, climate
science, biology, and more. Today's centers host heterogeneous architectures
and complex software stacks, exemplified by NERSC's Perlmutter system, which
combines CPU-only and GPU-accelerated nodes with high-speed storage and
networking. Supporting thousands of users on such platforms requires efficient
operations, responsive help desks, and automation for routine tasks.

At the same time, artificial intelligence is becoming a core component of
scientific workflows. Researchers increasingly rely on machine learning models
for data reduction, analysis, and simulation steering. This shift compounds the
operational burden: staff must troubleshoot AI tooling, curate datasets, and
manage rapid iteration cycles while maintaining traditional HPC services.

Agentic AI—systems that can reason, plan, and invoke tools—offers a path to
augment human operators. By coupling language models with domain-specific
tools, agents can triage incidents, retrieve documentation, and orchestrate
end-to-end workflows. However, HPC centers need a framework that is modular,
configurable, and adaptable to their unique environments.

ATHOS addresses this need by providing a registry-driven toolkit for composing
and evaluating agentic systems. The toolkit abstracts model selection, tool
integration, and flow orchestration so that new capabilities can be added
through configuration rather than bespoke code. This paper motivates the use of
agentic AI in HPC settings, details the design of ATHOS, and reports on early
experiments at NERSC leveraging ServiceNow and the Superfacility API. The
remainder of the outline sketches the planned sections and placeholders for
future results.

## 2. Motivation for Agentic AI in HPC Centers
- Complexity of modern systems like NERSC's Perlmutter supercomputer
- Rapid growth of AI and data-driven scientific workflows
- Challenges in user support, incident response, and operational efficiency
- Rise of agentic AI systems granting LLMs capabilities in reflection, tool use,
  planning, and multi-agent collaboration
- Release of the Model Context Protocol (MCP) standard from Anthropic, enabling
  an ecosystem of pluggable tools that connect LLMs to services
- Benefits of these capabilities for monitoring, ticket triage, and workflow
  automation across HPC operations

## 3. ATHOS Toolkit Overview
ATHOS is designed as a lightweight yet expressive toolkit that lets practitioners
compose agentic systems from interchangeable parts rather than monolithic
applications. Configuration files describe the desired flows, models, and tools,
and a registry architecture discovers new capabilities when their modules are
imported. At runtime, registries expose these extensions to the rest of the
system so that agents can be assembled without modifying core source code.

Factory utilities interpret the YAML configuration and construct the required
models, tools, and Model Context Protocol (MCP) clients. Because these factories
are model-agnostic, the same workflow can swap between open and proprietary
language models or interface with HPC-specific tools such as SLURM and
ServiceNow. A small command-line interface ties these pieces together, enabling
developers to launch flows, run experiments, and iterate on new agent behaviors
from the terminal.

## 4. System Design and Features
The heart of ATHOS is a set of flow classes—such as `AgentFlow` for general task
automation and `LangGraphChatbotFlow` for conversational assistance—that coordinate model
reasoning, tool invocation, and state management. These flows leverage the
`flow_registry`, which acts as the discovery mechanism and extension point for
new behaviors. Through `athos.runtime.builder.build_config` and `build_flow`, configurations
are transformed into runnable agents that are consistent across environments,
while tool integrations are instantiated directly from their configuration
definitions.

Integration is achieved through MCP-aware tool servers that bridge ATHOS with
external services like ServiceNow for ticket management, SLURM for job control,
and the Superfacility API for data movement and orchestration. The framework also
supports multi-agent compositions and optional human approval steps, and it runs
on top of both the OpenAI Agents SDK and Hugging Face SmolAgents to accommodate
diverse model backends.

## 5. Deployment at NERSC
- Current testing at NERSC with the Perlmutter supercomputer
- Leveraging ServiceNow for user support ticket integration
- Accessing data center and workflow endpoints via the Superfacility API

## 6. Evaluation Framework
- `evals/run_evaluations.py` script executes flows on curated test cases and QA pairs
- Test cases in `evals/test_cases` combine user descriptions, files, and reference solutions
- LLM-based evaluator scores responses on a 0–100 scale with feedback
- Computes average score and pass rate against a configurable threshold
- Supports benchmarking different flows and models through a unified interface

## 7. Example Workflows (Placeholders)
- **HPC Chatbot**: answering user questions and guiding job submissions
- **ServiceNow Agent**: triaging incidents and suggesting resolutions
- **Superfacility Orchestrator**: managing data transfers and workflow execution
- Additional workflows to be detailed in future revisions

## 8. Results (Placeholders)
- Performance of ATHOS agents on support ticket classification
- Reduction in time-to-resolution for common incidents
- Impact on throughput for data movement workflows
- Full results will be populated as testing progresses

## 9. Related Work
- Overview of existing agent frameworks and AI-driven support systems
- Comparison with other HPC automation tools

## 10. Conclusion and Future Work
- Summary of ATHOS contributions and potential
- Future directions: scaling to other DOE facilities, expanding tool ecosystem
- Toward self-optimizing, agent-driven HPC operations


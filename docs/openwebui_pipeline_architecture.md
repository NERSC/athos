# OpenWebUI Pipeline Architecture: Hierarchical Session Management

This document details the architectural approach for managing sessions within ATHOS, particularly focusing on how the ATHOS `SessionStore` integrates with framework-specific persistence mechanisms like LangGraph's checkpointing.

## Two-Level Session Persistence Strategy

To provide both application-level session management and support for complex, stateful flows (e.g., LangGraph), ATHOS employs a two-level persistence strategy:

1.  **ATHOS `SessionStore` (Primary Layer):**
    *   **Purpose:** Manages the overall application-level session, providing a unified interface for session lifecycle, metadata, and user experience features.
    *   **Content:** Stores general session information such as conversational chat history, creation timestamps, Time-To-Live (TTL) settings, and user-specific metadata. Crucially, for stateful flows, it stores a **pointer** or **identifier** to the underlying framework's saved state.
    *   **Implementation:** As per Milestone M1, this will be backed by a Redis instance, offering configurable TTL and centralized management.

2.  **Framework-Specific Persistence (Secondary Layer):**
    *   **Purpose:** Handles the detailed, internal state serialization and deserialization for specific agent frameworks.
    *   **Content:** Stores the complex internal state of a running flow, such as the graph's current node, task states, and intermediate values.
    *   **Example (LangGraph):** LangGraph's native checkpointing mechanism, which saves the graph's state, typically identified by a `thread_id` or `configurable` key. This can also be configured to use a Redis backend, potentially sharing the same Redis instance as the ATHOS `SessionStore` but using distinct key prefixes.

## Session Resume Workflow

When a user interacts with a previously started session, the `FlowRunner` orchestrates the resume process using this two-level strategy:

1.  **Request Reception:** A user request arrives at the `FlowRunner`, typically including an ATHOS `session_id`.
2.  **ATHOS Session Retrieval:** The `FlowRunner` queries the **ATHOS `SessionStore`** using the provided `session_id`.
3.  **Pointer Extraction:** The `SessionStore` returns the application-level session data. For a LangGraph-based flow, this data will include a `langgraph_thread_id` (or similar identifier) which acts as the pointer to the LangGraph's saved state.
4.  **LangGraph Initialization:** The `FlowRunner` initializes the LangGraph flow. During this initialization, it passes the extracted `langgraph_thread_id` to the LangGraph runtime.
5.  **LangGraph State Loading:** LangGraph's native checkpointing mechanism, upon receiving the `thread_id`, automatically loads the corresponding detailed graph state from its configured persistence backend.
6.  **Flow Resumption:** With its internal state restored, the LangGraph flow is fully resumed and can seamlessly continue processing the new user input from its last known state.

## Benefits of this Approach

*   **Decoupling:** The ATHOS `SessionStore` remains lightweight and framework-agnostic, only needing to store a pointer to the framework's state, rather than understanding its complex internal structure.
*   **Flexibility:** This model accommodates different types of flows. A stateless flow might not require a framework-specific pointer, while a LangGraph flow will.
*   **Centralized Metadata & UX:** All sessions benefit from the centralized management of chat history, TTL, and other application-level features provided by the ATHOS `SessionStore`.
*   **Operational Control:** Allows for unified configuration, monitoring, and tooling (e.g., migration scripts, health checks) for all sessions within the ATHOS ecosystem.

This hierarchical approach ensures robust, flexible, and maintainable session management across diverse agentic workflows within ATHOS.
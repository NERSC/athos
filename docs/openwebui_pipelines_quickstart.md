# OpenWebUI Pipelines Quickstart

This guide explains how to launch the official OpenWebUI Pipelines and UI
containers alongside the Athos hello-world pipeline. The goal is to offer
a concrete starting point before wiring real Athos flows into Pipelines.

## What the demo provides

- **Hello-world manifold pipeline** – exposes two mock "models" that
  respond with friendly or formal greetings so you can verify that
  multiple pipeline models appear in OpenWebUI.
- **Official container images** – uses `ghcr.io/open-webui/open-webui:main`
  and `ghcr.io/open-webui/pipelines:main` straight from the OpenWebUI team.
- **Minimal configuration** – a single `docker compose` file and a
  mounted pipeline script.

## Prerequisites

- Docker and Docker Compose v2 (or the standalone `docker-compose` CLI).
- Ports `3000` (OpenWebUI) and `9099` (Pipelines) available locally.

## Launching the stack

1. **Start both services**

   ```bash
   docker compose -f integrations/openwebui/docker-compose.yml up --build
   ```

   The compose file mounts `integrations/openwebui/pipelines` into the
   Pipelines container, so any edits to the pipeline scripts are picked up
   on the next container restart.

2. **Open the UI** – navigate to <http://localhost:3000>. Authentication is
   disabled by default for the demo via `WEBUI_AUTH=False`.

3. **Point OpenWebUI at Pipelines**

   - Open **Settings → Connections → OpenAI API**.
   - Set the **API URL** to `http://pipelines:9099` if you are using the
     Docker network, or `http://localhost:9099` when connecting from your
     host.
   - Set the **API Key** to `0p3n-w3bu!` (the Pipelines default).
   - Save the connection.

4. **Chat using the demo models**

   - Create a new chat and select either `Athos Hello (Friendly)` or
     `Athos Hello (Formal)` from the model selector.
   - Send a prompt and observe the deterministic greeting that comes back.
     Streaming is supported, so you should see tokens arrive incrementally
     when the chat is configured for streaming responses.

To stop the services, run `docker compose -f integrations/openwebui/docker-compose.yml down`.

## File layout

```
integrations/openwebui/
├── docker-compose.yml           # Launches the official UI + Pipelines containers
└── pipelines/
    └── athos_hello_world_manifold_pipeline.py
```

The pipeline script follows the OpenWebUI Pipelines "manifold" protocol.
It returns static responses today, but the structure mirrors what we will
use when Athos flows are available.

## Next steps toward Athos integration

1. **Bridge to FlowRunner** – replace the static greeting logic with
   calls into the Athos FlowRunner so that pipeline "models" correspond to
   registered Athos flows.
2. **Event formatting** – emit structured status and artifact events via
   the pipelines streaming API to mirror Athos FlowOutput metadata.
3. **Session persistence** – map OpenWebUI chat sessions onto Athos
   `FlowSession` instances so that multi-turn state is preserved.
4. **Valve-backed configuration** – allow the pipeline valves to control
   FlowRunner configuration (e.g., selecting which flow to call or toggling
   tracing providers).
5. **Automated tests** – add integration tests that hit the pipeline
   endpoints locally to validate streaming, error handling, and valve
   updates without needing the full UI.

Refer to `docs/athos_openwebui_integration_plan_v3.0.md` for the broader
architecture roadmap. This quickstart intentionally focuses on the
minimum viable bridge required for experimentation.

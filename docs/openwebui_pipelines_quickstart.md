# OpenWebUI Pipelines Quickstart

This guide explains how to launch the official OpenWebUI Pipelines and UI
containers alongside two Athos pipeline implementations:

- A FlowRunner-backed manifold pipeline that exposes real Athos flows as
  selectable OpenWebUI models.
- The original hello-world manifold pipeline that remains available as a
  lightweight reference implementation.

## What the demo provides

- **FlowRunner manifold pipeline** – bridges the Athos FlowRunner into
  OpenWebUI so each configured flow can be surfaced as a pipeline model.
  The pipeline honours `config/config.yaml`, streams responses when
  supported, and formats `FlowOutput` artifacts for the chat UI.
- **Hello-world manifold pipeline** – still available for quick
  experimentation or as a template for new pipelines.
- **Custom pipelines image** – a small derivative of
  `ghcr.io/open-webui/pipelines:main` that pre-installs the Athos package,
  ensuring FlowRunner dependencies are present at container start-up.

## Prerequisites

- Docker and Docker Compose v2 (or the standalone `docker-compose` CLI).
- Ports `3000` (OpenWebUI) and `9099` (Pipelines) available locally.

## Launching the stack

1. **Start both services**

   ```bash
   docker compose -f integrations/openwebui/docker-compose.yml up --build
   ```

   The compose file mounts `integrations/openwebui/pipelines` into the
   Pipelines container and rebuilds a local image that already includes the
   Athos package. Any edits to the pipeline scripts are picked up on the
   next container restart.

2. **Open the UI** – navigate to <http://localhost:3000>. Authentication is
   disabled by default for the demo via `WEBUI_AUTH=False`.

3. **Point OpenWebUI at Pipelines**

   - Open **Settings → Connections → OpenAI API**.
   - Set the **API URL** to `http://pipelines:9099` if you are using the
     Docker network, or `http://localhost:9099` when connecting from your
     host.
   - Set the **API Key** to `0p3n-w3bu!` (the Pipelines default).
   - Save the connection.

4. **Chat using Athos flows**

   - Create a new chat and select one of the models exposed by the
     FlowRunner pipeline (for example `Chatbot that answers general HPC
     questions (hpc_chatbot)`).
   - Provide any required credentials (such as `CBORG_API_KEY`) in your
     environment or `.env` file so the selected flow can reach its backing
     model.
   - Streaming responses are enabled by default; OpenWebUI will receive
     incremental tokens whenever the underlying flow supports streaming.

   The hello-world pipeline remains available if you want a deterministic
   demonstration model while configuring Athos credentials.

To stop the services, run `docker compose -f integrations/openwebui/docker-compose.yml down`.

## File layout

```
integrations/openwebui/
├── Dockerfile.pipelines          # Builds a pipelines image with the Athos wheel pre-installed
├── docker-compose.yml            # Launches the customized pipelines + official UI containers
└── pipelines/
    ├── athos_flowrunner_manifold_pipeline.py   # FlowRunner-backed manifold pipeline
    └── athos_hello_world_manifold_pipeline.py  # Reference hello-world pipeline
```

The repository-level `.dockerignore` keeps the build context lean when
Compose rebuilds the pipelines image.

The FlowRunner pipeline is a thin adapter that translates OpenWebUI
requests into `FlowRunner.execute()` or `FlowRunner.stream()` calls and
formats `FlowOutput` data for the UI. The hello-world script remains a
simple example for experimentation.

## Configuring Athos flows

The FlowRunner pipeline reads the standard Athos configuration file.
Update `config/config.yaml` and provide any required environment variables
before launching the stack. Key valves exposed in OpenWebUI (and via
environment variables with the `ATHOS_PIPELINE_` prefix) include:

- `config_path` – absolute path to the Athos configuration file inside the
  container (defaults to `/workspace/config/config.yaml`).
- `enabled_flows` – comma-delimited list of flows to expose as models. If
  left empty, every flow defined in the config becomes available.
- `default_flow` – fallback flow used when the requested model ID is not
  recognised.
- `enable_streaming` – toggle streaming output if a flow should only return
  full responses.

## Next steps toward Athos integration

1. **Artifact-rich streaming** – extend the streaming bridge to emit
   structured status events and richer artifact metadata as new FlowRunner
   hooks become available.
2. **Session persistence** – replace the in-memory session store with a
   persistent backend so conversations survive pipeline restarts.
3. **Valve expansion** – expose additional FlowRunner controls (such as
   tracing providers or tool access) through pipeline valves.
4. **Automated tests** – add integration tests that hit the pipeline
   endpoints locally to validate streaming, error handling, and valve
   updates without needing the full UI.

Refer to `docs/athos_openwebui_integration_plan_v3.0.md` for the broader
architecture roadmap. This quickstart intentionally focuses on the
minimum viable bridge required for experimentation.

"""OpenWebUI manifold pipeline backed by the Athos FlowRunner."""

import asyncio
import contextlib
import json
import logging
import os
import time
import uuid
from typing import (
    Any,
    Awaitable,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner
from athos.models.flow import FlowOutput

logger = logging.getLogger(__name__)


class Pipeline:
    """Expose multiple Athos flows as OpenWebUI models."""

    class Valves(BaseModel):
        """User-configurable settings surfaced in the Pipelines UI."""

        config_path: str = Field(
            default="/workspace/config/config.yaml",
            description="Absolute path to the Athos configuration file.",
        )
        default_flow: str = Field(
            default="hpc_chatbot",
            description="Flow to use when the selected model is unavailable.",
        )
        enabled_flows: List[str] = Field(
            default_factory=list,
            description="Subset of flows to expose. Leave empty to expose all flows from the config.",
        )
        enable_streaming: bool = Field(
            default=True,
            description="Stream tokens back to OpenWebUI when flows support it.",
        )

    def __init__(self) -> None:
        self.type = "manifold"
        self.name = "ATHOS"
        self.version = "0.2.0"
        self.description = "Expose configured Athos flows via the FlowRunner."
        self.author = "Athos Team"

        self.valves = self.Valves(**self._read_env_overrides())

        self.pipelines: List[Dict[str, str]] = []
        self._available_flows: List[str] = []
        self._runner: Optional[FlowRunner] = None
        self._initialized = False

    async def on_startup(self) -> None:
        """Load Athos configuration and prepare the FlowRunner."""

        await self._initialize_runner()

    async def on_shutdown(self) -> None:
        """Release FlowRunner resources on shutdown."""

        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
        self._initialized = False

    async def on_valves_updated(self) -> None:
        """Rebuild runner state after valve changes."""

        await self._initialize_runner(force_reload=True)

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[
        dict,
        str,
        Generator[str, None, None],
        Iterator[str],
        Iterable[str],
    ]:
        """Entrypoint invoked by OpenWebUI for every chat completion request."""

        del messages  # FlowRunner tracks history via FlowSession persistence.

        if not self._initialized:
            try:
                self._run_in_loop(self._initialize_runner())
            except Exception as exc:  # noqa: BLE001 - surface initialization errors to the UI
                logger.exception("Failed to initialize Athos FlowRunner pipeline")
                model = model_id or self.valves.default_flow
                return self._build_error_response(model, f"Initialization error: {exc}")

        flow_name = self._resolve_flow_name(model_id)
        user_id = self._resolve_user_id(body)
        session_id = self._resolve_session_id(body)
        metadata = {"model_id": flow_name, "source": "openwebui"}

        stream_requested = bool(body.get("stream", self.valves.enable_streaming))
        if stream_requested and self.valves.enable_streaming:
            return self._stream_flow(
                flow_name=flow_name,
                message=user_message,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata,
            )

        return self._run_sync_flow(
            flow_name=flow_name,
            message=user_message,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

    async def _initialize_runner(self, *, force_reload: bool = False) -> None:
        """Instantiate FlowRunner and derive available flows."""

        if self._initialized and not force_reload:
            return

        config_path = self.valves.config_path
        logger.info("Loading Athos configuration from %s", config_path)

        config = build_config(config_path)
        if not config.flows:
            raise RuntimeError("Athos configuration does not define any flows")

        if self._runner is not None:
            await self._runner.cleanup()

        self._runner = FlowRunner(config)
        self._available_flows = sorted(config.flows.keys())

        enabled = [flow for flow in self.valves.enabled_flows if flow in self._available_flows]
        if not enabled:
            enabled = list(self._available_flows)

        self.pipelines = [
            {
                "id": flow,
                "name": f": {flow}",
                #"name": self._format_flow_name(flow, getattr(config.flows[flow], "description", None)),
            }
            for flow in enabled
        ]

        if not self.pipelines:
            raise RuntimeError("No flows selected for exposure in the manifold pipeline")

        first_flow = self.pipelines[0]["id"]
        if self.valves.default_flow not in {p["id"] for p in self.pipelines}:
            logger.warning(
                "Default flow '%s' is not available; falling back to '%s'",
                self.valves.default_flow,
                first_flow,
            )
            self.valves.default_flow = first_flow

        self._initialized = True
        logger.info("Athos FlowRunner pipeline initialized with flows: %s", ", ".join(self._flow_ids))

    @property
    def _flow_ids(self) -> List[str]:
        return [p["id"] for p in self.pipelines]

    def _resolve_flow_name(self, model_id: str) -> str:
        if model_id in self._flow_ids:
            return model_id
        logger.debug("Unknown model '%s'; using default flow '%s'", model_id, self.valves.default_flow)
        return self.valves.default_flow

    @staticmethod
    def _resolve_user_id(body: dict) -> str:
        user = body.get("user") or {}
        return str(user.get("id") or "openwebui-user")

    @staticmethod
    def _resolve_session_id(body: dict) -> str:
        chat_id = body.get("chat_id")
        if chat_id:
            return str(chat_id)
        return f"chat-{int(time.time())}"

    def _run_sync_flow(
        self,
        *,
        flow_name: str,
        message: str,
        session_id: str,
        user_id: str,
        metadata: Dict[str, Any],
    ) -> dict:
        if self._runner is None:
            raise RuntimeError("FlowRunner is not initialized")

        result = self._run_in_loop(
            self._runner.execute(
                flow_name=flow_name,
                message=message,
                session_id=session_id,
                user_id=user_id,
                interface="openwebui",
                metadata=metadata,
            )
        )

        if not result.success or result.output is None:
            error_message = result.error or "Unknown error"
            logger.error("Flow '%s' execution failed: %s", flow_name, error_message)
            return self._build_error_response(flow_name, error_message)

        content = self._format_output(result.output)
        return self._build_sync_response(flow_name, content)

    def _stream_flow(
        self,
        *,
        flow_name: str,
        message: str,
        session_id: str,
        user_id: str,
        metadata: Dict[str, Any],
    ) -> Generator[str, None, None]:
        if self._runner is None:
            raise RuntimeError("FlowRunner is not initialized")

        chunk_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())

        def generator() -> Generator[str, None, None]:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                stream = self._runner.stream(
                    flow_name=flow_name,
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    interface="openwebui",
                    metadata=metadata,
                )
                try:
                    while True:
                        try:
                            output = loop.run_until_complete(stream.__anext__())
                        except StopAsyncIteration:
                            break
                        except Exception as exc:  # noqa: BLE001 - propagate structured error event
                            logger.exception("Streaming flow '%s' failed", flow_name)
                            yield self._build_stream_error(chunk_id, created, flow_name, str(exc))
                            break

                        if output.metadata.get("error"):
                            yield self._build_stream_error(chunk_id, created, flow_name, output.content)
                            break

                        if output.metadata.get("streaming") and output.metadata.get("chunk"):
                            if output.content:
                                yield self._build_stream_chunk(chunk_id, created, flow_name, output.content)
                            continue

                        final_content = self._format_output(output)
                        yield self._build_stream_final(chunk_id, created, flow_name, final_content)
                        break
                finally:
                    with contextlib.suppress(Exception):
                        loop.run_until_complete(stream.aclose())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

            yield "data: [DONE]\n\n"

        return generator()

    def _build_sync_response(self, model_id: str, content: str) -> dict:
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
        }

    def _build_error_response(self, model_id: str, error: str) -> dict:
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": f"Error: {error}"},
                }
            ],
        }

    def _build_stream_chunk(self, chunk_id: str, created: int, model_id: str, content: str) -> str:
        data = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": None,
                }
            ],
        }
        return f"data: {json.dumps(data)}\n\n"

    def _build_stream_final(self, chunk_id: str, created: int, model_id: str, content: str) -> str:
        data = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": "stop",
                }
            ],
        }
        return f"data: {json.dumps(data)}\n\n"

    def _build_stream_error(self, chunk_id: str, created: int, model_id: str, error: str) -> str:
        return self._build_stream_final(chunk_id, created, model_id, f"Error: {error}")

    def _format_output(self, output: FlowOutput) -> str:
        parts = [output.content]
        for artifact in output.artifacts:
            if artifact.type == "image" and artifact.path:
                parts.append(f"\n\n![{artifact.display_name or 'image'}]({artifact.path})")
            elif artifact.type == "file" and artifact.path:
                parts.append(f"\n\n📄 [{artifact.display_name or 'file'}]({artifact.path})")
            elif artifact.type == "link" and artifact.data:
                parts.append(f"\n\n🔗 [{artifact.display_name or 'link'}]({artifact.data})")
        return "".join(parts)

    def _format_flow_name(self, flow: str, description: Optional[str]) -> str:
        if description:
            return f"{description} ({flow})"
        return flow.replace("_", " ").title()

    @staticmethod
    def _run_in_loop(coro: Awaitable[Any]) -> Any:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    def _read_env_overrides(self) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        for field_name, field in self.Valves.model_fields.items():
            env_name = f"ATHOS_PIPELINE_{field_name.upper()}"
            raw = os.getenv(env_name)
            if raw is None:
                continue

            annotation = field.annotation
            origin = get_origin(annotation)
            if origin is Union:
                args = [arg for arg in get_args(annotation) if arg is not type(None)]
                if len(args) == 1:
                    annotation = args[0]
                    origin = get_origin(annotation)

            if annotation is bool:
                overrides[field_name] = raw.lower() in {"1", "true", "yes", "on"}
                continue

            if origin in {list, List} or annotation in (List[str], list):
                overrides[field_name] = [item.strip() for item in raw.split(",") if item.strip()]
                continue

            overrides[field_name] = raw
        return overrides


__all__ = ["Pipeline"]

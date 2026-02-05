"""Flow runner responsible for orchestrating flow execution."""

from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, Optional, Union

from athos.config.models import AthosConfig
from athos.interfaces.base_flow import BaseFlow
from athos.models.enums import ExecutionMode
from athos.models.execution import FlowRequest, FlowResult
from athos.models.flow import FlowInput, FlowOutput
from athos.models.message import Message, MessageRole
from athos.models.metrics import ExecutionMetrics
from athos.models.session import FlowSession
from athos.runtime.builder import build_flow
from athos.runtime.session_store import InMemorySessionStore, SessionStore

logger = logging.getLogger(__name__)


class FlowRunner:
    """Coordinate flow lifecycle, session management, and execution."""

    def __init__(
        self,
        config: AthosConfig,
        session_store: Optional[SessionStore] = None,
    ) -> None:
        self.config = config
        self.session_store = session_store or InMemorySessionStore()
        self._flow_cache: Dict[str, BaseFlow] = {}

    async def execute(
        self,
        flow_name: str,
        message: Union[str, Message],
        session_id: str,
        user_id: str,
        *,
        mode: ExecutionMode = ExecutionMode.SYNC,
        interface: str = "unknown",
        metadata: Optional[dict] = None,
    ) -> FlowResult:
        """Execute a flow synchronously and capture structured results."""

        normalized_message = self._coerce_message(message)
        request = FlowRequest(
            request_id=self._generate_request_id(),
            flow_name=flow_name,
            message=normalized_message,
            session_id=session_id,
            user_id=user_id,
            mode=mode,
            metadata=metadata or {},
        )

        logger.info(
            "[%s] Executing flow '%s' for user=%s session=%s",
            request.request_id,
            flow_name,
            user_id,
            session_id,
        )

        start_time = time.time()

        try:
            session = await self._ensure_session(
                session_id=session_id,
                user_id=user_id,
                interface=interface,
            )
            flow = await self._get_flow(flow_name)
            logger.debug(f"FlowRunner.execute history: {session.get_history()}")
            flow_input = FlowInput(
                message=normalized_message,
                session=session,
                mode=mode,
                metadata=metadata or {},
            )

            logger.debug("[%s] Calling flow.execute()", request.request_id)
            output = await flow.execute(flow_input)

            self._record_interaction(session, normalized_message, output.content)
            await self.session_store.save(session)

            execution_time = time.time() - start_time
            metrics = ExecutionMetrics.from_output_metadata(output.metadata)
            result_metadata = {"flow_name": flow_name}
            if metrics:
                metrics.latency_ms = execution_time * 1000
                result_metadata.update(metrics.to_metadata())
            else:
                result_metadata["latency_ms"] = execution_time * 1000

            result = FlowResult(
                request_id=request.request_id,
                session_id=session.session_id,
                success=True,
                output=output,
                error=None,
                execution_time=execution_time,
                metadata=result_metadata,
            )

            logger.info(
                "[%s] Flow '%s' succeeded in %.2fs",
                request.request_id,
                flow_name,
                execution_time,
            )
            self._log_metrics(flow_name, result_metadata)
            logger.debug(
                "[%s] Flow '%s' result metadata: %s",
                request.request_id,
                flow_name,
                result_metadata,
            )

            return result

        except Exception as exc:  # noqa: BLE001 - surface all failures
            execution_time = time.time() - start_time
            logger.exception(
                "[%s] Flow '%s' failed after %.2fs: %s",
                request.request_id,
                flow_name,
                execution_time,
                exc,
            )

            return FlowResult(
                request_id=request.request_id,
                session_id=request.session_id,
                success=False,
                output=None,
                error=str(exc),
                execution_time=execution_time,
                metadata={
                    "flow_name": flow_name,
                    "exception_type": type(exc).__name__,
                },
            )

    async def stream(
        self,
        flow_name: str,
        message: Union[str, Message],
        session_id: str,
        user_id: str,
        *,
        interface: str = "unknown",
        metadata: Optional[dict] = None,
    ) -> AsyncGenerator[FlowOutput, None]:
        """Execute a flow with streaming semantics."""

        normalized_message = self._coerce_message(message)
        request = FlowRequest(
            request_id=self._generate_request_id(),
            flow_name=flow_name,
            message=normalized_message,
            session_id=session_id,
            user_id=user_id,
            mode=ExecutionMode.STREAMING,
            metadata=metadata or {},
        )

        logger.info(
            "[%s] Streaming flow '%s' for user=%s session=%s",
            request.request_id,
            flow_name,
            user_id,
            session_id,
        )

        session = await self._ensure_session(
            session_id=session_id,
            user_id=user_id,
            interface=interface,
        )
        flow = await self._get_flow(flow_name)

        logger.debug(f"FlowRunner.stream history: {session.get_history()}")

        start_time = time.time()

        if not flow.can_stream():
            logger.warning(
                "[%s] Flow '%s' does not support streaming; falling back to execute()",
                request.request_id,
                flow_name,
            )
            output = await flow.execute(
                FlowInput(
                    message=normalized_message,
                    session=session,
                    mode=ExecutionMode.SYNC,
                    metadata=metadata or {},
                )
            )
            output_metadata = dict(output.metadata)
            output_metadata.setdefault("streaming", False)
            output_metadata["final"] = True
            output_metadata.setdefault("latency_ms", (time.time() - start_time) * 1000)
            final_output = FlowOutput(
                content=output.content,
                artifacts=list(output.artifacts),
                metadata=output_metadata,
            )
            self._log_metrics(flow_name, output_metadata)
            self._record_interaction(session, normalized_message, output.content)
            await self.session_store.save(session)
            yield final_output
            return

        flow_input = FlowInput(
            message=normalized_message,
            session=session,
            mode=ExecutionMode.STREAMING,
            metadata=metadata or {},
        )

        buffered_chunks: list[str] = []
        emitted_any_chunk = False
        try:
            async for output in flow.stream(flow_input):
                emitted_any_chunk = True
                if output.metadata.get("final"):
                    output.metadata.setdefault("latency_ms", (time.time() - start_time) * 1000)
                    self._log_metrics(flow_name, output.metadata)
                if output.content:
                    buffered_chunks.append(output.content)
                # Refer to docs/athos_openwebui_integration_plan_v3.0.md#streaming-contract
                # for the expected metadata flags emitted with each FlowOutput chunk.
                yield output
        except Exception:
            logger.exception("[%s] Streaming flow '%s' failed", request.request_id, flow_name)
            raise
        else:
            logger.info("[%s] Streaming flow '%s' completed", request.request_id, flow_name)
        finally:
            if emitted_any_chunk:
                self._record_interaction(session, normalized_message, "".join(buffered_chunks))
                await self.session_store.save(session)

    async def cleanup(self) -> None:
        """Cleanup all cached flow instances."""

        logger.info("Cleaning up %d cached flows", len(self._flow_cache))
        for flow_name, flow in list(self._flow_cache.items()):
            try:
                await flow.cleanup()
            except Exception as exc:  # noqa: BLE001 - log and continue cleanup
                logger.warning("Error cleaning up flow '%s': %s", flow_name, exc)
        self._flow_cache.clear()

    async def _ensure_session(
        self,
        *,
        session_id: str,
        user_id: str,
        interface: str,
    ) -> FlowSession:
        """Retrieve or create a session with workspace metadata."""

        return await self.session_store.get_or_create(
            session_id=session_id,
            user_id=user_id,
            workspace=self._get_workspace_path(user_id, session_id),
            interface=interface,
        )

    async def _get_flow(self, flow_name: str) -> BaseFlow:
        """Return a cached flow instance or build a new one.

        All flows are built using the create() classmethod pattern and are
        fully initialized when returned from build_flow().
        """

        if flow_name in self._flow_cache:
            return self._flow_cache[flow_name]

        if flow_name not in self.config.flows:
            raise ValueError(f"Unknown flow: {flow_name}")

        # Build flow using create() classmethod
        logger.debug("Loading flow '%s'", flow_name)
        flow = await build_flow(flow_name, self.config)

        self._flow_cache[flow_name] = flow
        logger.info("Flow '%s' loaded and cached", flow_name)
        return flow

    def _record_interaction(self, session: FlowSession, message: Message, response: str) -> None:
        """Persist user ↔ assistant messages into the session."""

        session.add_message(message)
        session.add_assistant_message(response)

    @staticmethod
    def _metrics_log_level() -> int:
        level_name = os.getenv("ATHOS_METRICS_LOG_LEVEL", "INFO").upper()
        return logging._nameToLevel.get(level_name, logging.INFO)

    def _log_metrics(self, flow_name: str, metadata: dict) -> None:
        level = self._metrics_log_level()
        if not logger.isEnabledFor(level):
            return

        token_usage = metadata.get("token_usage")
        latency_ms = metadata.get("latency_ms")
        tool_calls = metadata.get("tool_calls") or []

        input_tokens = None
        output_tokens = None
        total_tokens = None
        if isinstance(token_usage, dict):
            input_tokens = token_usage.get("input_tokens")
            output_tokens = token_usage.get("output_tokens")
            if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                total_tokens = input_tokens + output_tokens

        tool_names = [str(name) for name in tool_calls] if isinstance(tool_calls, list) else []
        tool_count = len(tool_names)

        if (
            input_tokens is None
            and output_tokens is None
            and latency_ms is None
            and tool_count == 0
        ):
            return

        tool_limit_raw = os.getenv("ATHOS_METRICS_TOOL_NAMES_LIMIT", "5")
        try:
            tool_limit = int(tool_limit_raw)
        except ValueError:
            tool_limit = 5

        truncated = False
        if tool_limit >= 0 and tool_count > tool_limit:
            tool_names = tool_names[:tool_limit]
            truncated = True

        logger.log(
            level,
            "metrics flow=%s latency_ms=%s input_tokens=%s output_tokens=%s total_tokens=%s tool_calls=%s tool_names=%s tool_names_truncated=%s",
            flow_name,
            f"{latency_ms:.2f}" if isinstance(latency_ms, (int, float)) else latency_ms,
            input_tokens,
            output_tokens,
            total_tokens,
            tool_count,
            tool_names,
            truncated,
        )

    def _generate_request_id(self) -> str:
        """Generate a human-readable request identifier."""

        return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def _get_workspace_path(self, user_id: str, session_id: str) -> Path:
        """Derive the workspace path for a given session."""

        base_path = getattr(self.config, "workspace_path", None)
        if base_path is None:
            base_path = Path(self.config.workspace_dir)
        else:
            base_path = Path(base_path)
        return base_path / user_id / session_id

    def _coerce_message(self, message: Union[str, Message]) -> Message:
        """Normalize user input into a Message."""
        if isinstance(message, Message):
            return message
        return Message(role=MessageRole.USER, content=message)

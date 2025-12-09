import os
import tempfile
from types import SimpleNamespace

import pytest

from athos.frameworks.langgraph.flows.chatbot import LangGraphChatbotFlow
from athos.frameworks.smolagents.flows.agent import AgentFlow
from athos.models.enums import ExecutionMode
from athos.models.message import Message, MessageRole
from athos.models.metrics import ExecutionMetrics
from athos.runtime.runner import FlowRunner


pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_LLM_TESTS") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Set RUN_LIVE_LLM_TESTS=1 and OPENAI_API_KEY to run live token/latency test.",
)
async def test_live_openai_token_usage_and_latency():
    """Opt-in check that we can parse token usage and latency from live OpenAI calls."""
    try:
        from langchain_openai import ChatOpenAI
    except Exception as exc:  # pragma: no cover - import is optional for live test
        pytest.skip(f"langchain_openai not available: {exc}")

    try:
        from smolagents import OpenAIServerModel
    except Exception as exc:  # pragma: no cover - import is optional for live test
        pytest.skip(f"smolagents not available: {exc}")

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chat_model = ChatOpenAI(model_name=model_name, temperature=0)

    chatbot_flow = LangGraphChatbotFlow(
        model=chat_model,
        system_prompt=None,
        initial_history=None,
        full_config=None,
    )

    smol_model = OpenAIServerModel(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))
    smol_flow = AgentFlow(
        model=smol_model,
        tools=[],
        agent_type="code",
        mcp_clients=None,
        full_config=None,
        max_steps=4,
        verbosity_level=0,
    )

    class InlineRunner(FlowRunner):
        def __init__(self, flow):
            super().__init__(config=SimpleNamespace(workspace_dir=tempfile.mkdtemp()))
            self._inline_flow = flow

        async def _get_flow(self, flow_name: str):
            return self._inline_flow

    message = Message(role=MessageRole.USER, content="Say hello briefly.")

    # LangGraph chatbot via runner
    runner = InlineRunner(chatbot_flow)
    lg_result = await runner.execute(
        flow_name="live_chatbot",
        message=message,
        session_id="live-token-test",
        user_id="tester",
        mode=ExecutionMode.SYNC,
    )
    lg_metrics = ExecutionMetrics.from_output_metadata(lg_result.metadata)

    assert lg_metrics is not None, "Expected metrics from LangGraph flow"
    assert lg_metrics.token_usage is not None, "Token usage should be populated"
    assert lg_metrics.token_usage.total_tokens > 0, "Token totals should be positive"
    assert lg_metrics.latency_ms is not None and lg_metrics.latency_ms > 0, "Latency should be recorded"

    # SmolAgents via runner
    sm_runner = InlineRunner(smol_flow)
    sm_result = await sm_runner.execute(
        flow_name="live_smol_agent",
        message=message,
        session_id="live-token-smol",
        user_id="tester",
        mode=ExecutionMode.SYNC,
    )
    sm_metrics = ExecutionMetrics.from_output_metadata(sm_result.metadata)

    assert sm_metrics is not None, "Expected metrics from SmolAgents flow"
    assert sm_metrics.token_usage is not None, "Token usage should be populated"
    assert sm_metrics.token_usage.total_tokens > 0, "Token totals should be positive"
    assert sm_metrics.latency_ms is not None and sm_metrics.latency_ms > 0, "Latency should be recorded"

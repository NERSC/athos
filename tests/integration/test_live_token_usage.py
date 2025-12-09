import os

import pytest

from athos.frameworks.langgraph.flows.chatbot import LangGraphChatbotFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.message import Message, MessageRole
from athos.models.metrics import ExecutionMetrics
from athos.models.session import FlowSession


pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_LLM_TESTS") != "1" or not os.getenv("OPENAI_API_KEY"),
    reason="Set RUN_LIVE_LLM_TESTS=1 and OPENAI_API_KEY to run live token usage test.",
)
async def test_live_openai_token_usage_parsing():
    """Opt-in check that we can parse token usage from a real OpenAI response."""
    try:
        from langchain_openai import ChatOpenAI
    except Exception as exc:  # pragma: no cover - import is optional for live test
        pytest.skip(f"langchain_openai not available: {exc}")

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chat_model = ChatOpenAI(model_name=model_name, temperature=0)

    flow = LangGraphChatbotFlow(
        model=chat_model,
        system_prompt=None,
        initial_history=None,
        full_config=None,
    )

    session = FlowSession(session_id="live-token-test", user_id="tester")
    flow_input = FlowInput(
        message=Message(role=MessageRole.USER, content="Say hello briefly."),
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    output = await flow.execute(flow_input)
    metrics = ExecutionMetrics.from_output_metadata(output.metadata)

    assert metrics is not None, "Expected metrics from live flow output"
    assert metrics.token_usage is not None, "Token usage should be populated"
    assert metrics.token_usage.total_tokens > 0, "Token totals should be positive"

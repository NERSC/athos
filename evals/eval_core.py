"""Core evaluation helpers (scoring + parsing)."""

from __future__ import annotations

import json
import re
from typing import Optional, Tuple

from smolagents import ChatMessage


def evaluate_response(eval_model, solution: str, response: str) -> Tuple[Optional[int], str]:
    prompt = (
        "You are an evaluator. Compare the agent's response with the reference solution. "
        "Grade the response on a scale of 0 to 100, where 100 means it perfectly matches the expected solution. "
        "Provide your output as a JSON object with keys 'score' (integer) and 'feedback' (string). "
        "Reference solution:\n"
        f"{solution}\n\n"
        "Agent response:\n"
        f"{response}\n"
    )
    messages = [
        ChatMessage(role="system", content="You are an evaluation assistant."),
        ChatMessage(role="user", content=prompt),
    ]
    eval_resp = eval_model(messages)
    text = eval_resp.content

    def _parse_json(txt: str):
        """Attempt to parse JSON even if wrapped in markdown."""
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            pass
        # look for ```json ... ``` block
        md_match = re.search(r"```(?:json)?\n([\s\S]*?)```", txt)
        if md_match:
            inner = md_match.group(1)
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                pass
        # fallback: first {...} block
        obj_match = re.search(r"\{[\s\S]*\}", txt)
        if obj_match:
            inner = obj_match.group(0)
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                pass
        return None

    try:
        result = _parse_json(text)
    except Exception as e:
        print("FAILURE in evaluation parsing")
        print("Evaluator output:")
        print(text)
        raise e

    if result and isinstance(result, dict):
        score = result.get("score")
        feedback = result.get("feedback")
    else:
        score = None
        feedback = text
    return score, feedback

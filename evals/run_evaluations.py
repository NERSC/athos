#!/usr/bin/env python3
"""Evaluation script for ATHOS flows on test cases"""
import argparse
import asyncio
import json
import re
from pathlib import Path
import pprint

from athos.core.manager import create_athos_manager
from smolagents import ChatMessage

def load_test_cases(cases_dir: Path):
    tests = []
    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        desc_file = case_dir / "user_description.txt"
        sol_file = case_dir / "solution.md"
        files_dir = case_dir / "files"
        if not desc_file.exists() or not sol_file.exists():
            continue
        description = desc_file.read_text()
        solution = sol_file.read_text()
        tests.append({
            "name": case_dir.name,
            "description": description,
            "solution": solution,
            "files_dir": files_dir if files_dir.exists() else None,
        })
    return tests

def build_input(description: str, files_dir: Path):
    input_data = description.strip()
    if files_dir:
        blocks = []
        for f in sorted(files_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(files_dir.parent)
            content = f.read_text()
            blocks.append(f"### {rel}\n```\n{content}\n```")
        if blocks:
            input_data += "\n\nAttached files:\n" + "\n\n".join(blocks)
    return input_data

def evaluate_response(eval_model, solution: str, response: str):
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

    result = _parse_json(text)
    if result and isinstance(result, dict):
        score = result.get("score")
        feedback = result.get("feedback")
    else:
        score = None
        feedback = text
    return score, feedback

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--flow",
        nargs="+",
        required=True,
        help="One or more flow names to evaluate",
    )
    parser.add_argument("--cases-dir", default="evals/test_cases")
    parser.add_argument("--eval-model", default=None,
                        help="Model name for evaluation (from config models)")
    parser.add_argument("--output", default=None,
                        help="Optional output file for results JSON")
    args = parser.parse_args()

    manager = create_athos_manager(args.config)
    cases = load_test_cases(Path(args.cases_dir))

    all_results = {}

    for flow_name in args.flow:
        pprint.pprint(manager.describe_flow(flow_name))

        flow_config = manager.config.execution_flows[flow_name]
        eval_model_name = args.eval_model or flow_config.model
        try:
            # Lazily load the evaluation model if needed
            eval_model = manager._get_or_create_model(eval_model_name)
        except ValueError:
            print(
                f"Error: evaluation model '{eval_model_name}' not found in configuration"
            )
            continue

        results = []
        for case in cases:
            name = case["name"]
            desc = case["description"]
            sol = case["solution"]
            files_dir = case["files_dir"]
            input_data = build_input(desc, files_dir)
            try:
                response = asyncio.run(manager.execute_flow(flow_name, input_data))
            except Exception as e:
                response = f"Error executing flow: {e}"
            score, feedback = evaluate_response(eval_model, sol, response)
            results.append(
                {
                    "test_case": name,
                    "response": response,
                    "score": score,
                    "feedback": feedback,
                }
            )

        total = 0
        count = 0
        print(f"\nEvaluation Results for {flow_name}:")
        for r in results:
            s = r["score"]
            print(f"- {r['test_case']}: score={s}")
            if isinstance(s, (int, float)):
                total += s
                count += 1
        if count > 0:
            avg = total / count
            print(f"Average score for {flow_name}: {avg:.2f}\n")

        all_results[flow_name] = results

    if args.output:
        Path(args.output).write_text(json.dumps(all_results, indent=2))

if __name__ == "__main__":
    main()

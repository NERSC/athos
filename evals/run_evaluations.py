#!/usr/bin/env python3
"""Evaluation script for ATHOS flows on test cases"""
import argparse
import asyncio
import json
from pathlib import Path

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
    try:
        result = json.loads(text)
        score = result.get("score")
        feedback = result.get("feedback")
    except json.JSONDecodeError:
        score = None
        feedback = text
    return score, feedback

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--flow", required=True)
    parser.add_argument("--cases-dir", default="evals/test_cases")
    parser.add_argument("--eval-model", default=None,
                        help="Model name for evaluation (from config models)")
    parser.add_argument("--output", default=None,
                        help="Optional output file for results JSON")
    args = parser.parse_args()

    manager = create_athos_manager(args.config)
    if args.flow not in manager.flows:
        print(f"Error: flow '{args.flow}' not found in configuration")
        return

    flow_config = manager.config.execution_flows[args.flow]
    eval_model_name = args.eval_model or flow_config.model
    if eval_model_name not in manager.models:
        print(f"Error: evaluation model '{eval_model_name}' not found in configuration")
        return
    eval_model = manager.models[eval_model_name]

    cases = load_test_cases(Path(args.cases_dir))
    results = []
    for case in cases:
        name = case["name"]
        desc = case["description"]
        sol = case["solution"]
        files_dir = case["files_dir"]
        input_data = build_input(desc, files_dir)
        try:
            response = asyncio.run(manager.execute_flow(args.flow, input_data))
        except Exception as e:
            response = f"Error executing flow: {e}"
        score, feedback = evaluate_response(eval_model, sol, response)
        results.append({
            "test_case": name,
            "response": response,
            "score": score,
            "feedback": feedback,
        })

    total = 0
    count = 0
    print("\nEvaluation Results:")
    for r in results:
        s = r["score"]
        print(f"- {r['test_case']}: score={s}")
        if isinstance(s, (int, float)):
            total += s
            count += 1
    if count > 0:
        avg = total / count
        print(f"\nAverage score: {avg:.2f}\n")
    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
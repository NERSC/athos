#!/usr/bin/env python3
"""Evaluation script for ATHOS flows on test cases"""
import argparse
import asyncio
import json
import re
from pathlib import Path
import pprint

from smolagents import ChatMessage

from athos import build_config, build_flow
from athos.frameworks.smolagents import factories as smolagents_factories
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode


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
        tests.append(
            {
                "name": case_dir.name,
                "description": description,
                "solution": solution,
                "files_dir": files_dir if files_dir.exists() else None,
            }
        )
    return tests


def load_qa_cases(path: Path):
    """Load question/answer cases from a JSON Lines file."""
    cases = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(
                {
                    "name": data.get("name"),
                    "description": data.get("question"),
                    "solution": data.get("answer"),
                }
            )
    return cases


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


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--flow",
        nargs="+",
        required=True,
        help="One or more flow names to evaluate",
    )
    parser.add_argument(
        "--cases-dir",
        action="append",
        default=[],
        help="Directory containing test case subdirectories (can be used multiple times)",
    )
    parser.add_argument(
        "--qa-file",
        action="append",
        default=[],
        help="JSON Lines file with question/answer pairs (can be used multiple times)",
    )
    parser.add_argument(
        "--eval-model",
        default=None,
        help="Model name for evaluation (from config models)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file for results JSON",
    )
    parser.add_argument(
        "--passing-score",
        type=float,
        default=80.0,
        help="Score threshold for accuracy calculations",
    )
    args = parser.parse_args()

    if not args.cases_dir and not args.qa_file:
        args.cases_dir = ["evals/test_cases"]

    cfg = build_config(args.config)
    flows = {}
    for name in args.flow:
        flows[name] = await build_flow(name, cfg)
    print("Loaded flows:")
    print(flows)

    datasets = []
    for d in args.cases_dir:
        path = Path(d)
        datasets.append((path.name, load_test_cases(path)))
    for fpath in args.qa_file:
        path = Path(fpath)
        datasets.append((path.stem, load_qa_cases(path)))

    all_results = {fn: {} for fn in args.flow}

    for flow_name in args.flow:
        flow = flows[flow_name]
        flow_config = cfg.flows[flow_name]

        # Print flow config for debugging
        pprint.pprint(flow_config.model_dump())

        # Evaluator model
        eval_model_name = args.eval_model or flow_config.model
        if args.eval_model and args.eval_model not in cfg.models:
            raise ValueError(
                f"Evaluation model '{args.eval_model}' not found in config models"
            )
        eval_model_instance = smolagents_factories.build_model(
            cfg.models[eval_model_name]
        )

        for dataset_name, cases in datasets:
            results = []
            for case in cases:
                name = case["name"]
                desc = case["description"]
                sol = case["solution"]
                files_dir = case.get("files_dir")
                input_data = build_input(desc, files_dir)

                # Create a FlowSession for this test case
                workspace_path = Path(cfg.workspace_path) / "eval" / flow_name / dataset_name / name
                workspace_path.mkdir(parents=True, exist_ok=True)

                session = FlowSession(
                    session_id=f"eval_{flow_name}_{dataset_name}_{name}",
                    user_id="evaluator",
                    workspace=workspace_path,
                    interface="evaluation"
                )

                # Create FlowInput with the message
                flow_input = FlowInput(
                    message=input_data,
                    session=session,
                    mode=ExecutionMode.SYNC
                )

                try:
                    output = await flow.execute(flow_input)
                    response = output.content if isinstance(output, FlowOutput) else str(output)
                except Exception as e:
                    response = f"Error executing flow: {e}"
                score, feedback = evaluate_response(
                    eval_model_instance, sol, response
                )
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
            passes = 0
            print(f"\nEvaluation Results for {flow_name} on {dataset_name}:")
            for r in results:
                s = r["score"]
                print(f"- {r['test_case']}: score={s}")
                if isinstance(s, (int, float)):
                    total += s
                    count += 1
                    if s >= args.passing_score:
                        passes += 1
            if count > 0:
                avg = total / count
                acc = passes / count
                print(
                    f"Average score for {flow_name} on {dataset_name}: {avg:.2f}"
                )
                print(
                    f"Accuracy for {flow_name} on {dataset_name}: {acc:.2%}\n"
                )

            all_results[flow_name][dataset_name] = results

    for f in flows.values():
        try:
            await f.cleanup()
        except Exception as e:  # pragma: no cover - cleanup errors ignored
            print(f"Warning: failed to cleanup flow: {e}")

    if args.output:
        Path(args.output).write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

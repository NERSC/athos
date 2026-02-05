#!/usr/bin/env python3
"""Evaluation script for ATHOS flows on test cases"""
import argparse
import asyncio
import json
from pathlib import Path
import pprint
import subprocess
from datetime import datetime, timezone

from dotenv import load_dotenv

from athos import build_config
from athos.frameworks.smolagents import factories as smolagents_factories
from athos.models.enums import ExecutionMode
from athos.models.metrics import ExecutionMetrics
from athos.runtime.runner import FlowRunner

from eval_core import evaluate_response
from eval_io import build_input, load_qa_cases, load_test_cases

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
    load_dotenv()

    if not args.cases_dir and not args.qa_file:
        args.cases_dir = ["evals/test_cases"]

    cfg = build_config(args.config)
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parent.parent,
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_sha = None
    for name in args.flow:
        if name not in cfg.flows:
            raise ValueError(f"Flow '{name}' not found in config")

    runner = FlowRunner(cfg)
    print("Loaded flows:")
    print(args.flow)

    datasets = []
    for d in args.cases_dir:
        path = Path(d)
        datasets.append((path.name, load_test_cases(path)))
    for fpath in args.qa_file:
        path = Path(fpath)
        datasets.append((path.stem, load_qa_cases(path)))

    all_results = {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_sha": git_sha,
            "config": str(args.config),
            "flows": list(args.flow),
            "eval_model": args.eval_model,
            "cases_dir": list(args.cases_dir),
            "qa_file": list(args.qa_file),
            "passing_score": args.passing_score,
        },
        "flows": {fn: {} for fn in args.flow},
    }

    for flow_name in args.flow:
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
            latency_values: list[float] = []
            input_tokens_values: list[int] = []
            output_tokens_values: list[int] = []
            total_tokens_values: list[int] = []
            for case in cases:
                name = case["name"]
                desc = case["description"]
                sol = case["solution"]
                files_dir = case.get("files_dir")
                input_data = build_input(desc, files_dir)

                try:
                    result = await runner.execute(
                        flow_name=flow_name,
                        message=input_data,
                        session_id=f"eval_{flow_name}_{dataset_name}_{name}",
                        user_id="evaluator",
                        mode=ExecutionMode.SYNC,
                        interface="evaluation",
                    )
                    if result.success and result.output:
                        response = result.output.content
                    else:
                        response = f"Error executing flow: {result.error or 'Unknown error'}"
                    metrics = ExecutionMetrics.from_output_metadata(result.metadata)
                    metrics_payload = metrics.to_metadata() if metrics else {}
                    if not metrics_payload and isinstance(result.metadata, dict):
                        latency = result.metadata.get("latency_ms")
                        if isinstance(latency, (int, float)):
                            metrics_payload = {"latency_ms": latency}
                except Exception as e:
                    response = f"Error executing flow: {e}"
                    metrics_payload = {}
                score, feedback = evaluate_response(
                    eval_model_instance, sol, response
                )
                if isinstance(metrics_payload, dict):
                    latency = metrics_payload.get("latency_ms")
                    if isinstance(latency, (int, float)):
                        latency_values.append(float(latency))
                    token_usage = metrics_payload.get("token_usage")
                    if isinstance(token_usage, dict):
                        input_tokens = token_usage.get("input_tokens")
                        output_tokens = token_usage.get("output_tokens")
                        if isinstance(input_tokens, int):
                            input_tokens_values.append(input_tokens)
                        if isinstance(output_tokens, int):
                            output_tokens_values.append(output_tokens)
                        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                            total_tokens_values.append(input_tokens + output_tokens)
                results.append(
                    {
                        "test_case": name,
                        "response": response,
                        "score": score,
                        "feedback": feedback,
                        "metrics": metrics_payload,
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

            def _percentile(values: list[float], percentile: float) -> float | None:
                if not values:
                    return None
                ordered = sorted(values)
                index = int(round((percentile / 100) * (len(ordered) - 1)))
                return ordered[index]

            summary = {
                "avg_latency_ms": (sum(latency_values) / len(latency_values)) if latency_values else None,
                "p50_latency_ms": _percentile(latency_values, 50),
                "p90_latency_ms": _percentile(latency_values, 90),
                "total_input_tokens": sum(input_tokens_values) if input_tokens_values else 0,
                "total_output_tokens": sum(output_tokens_values) if output_tokens_values else 0,
                "total_tokens": sum(total_tokens_values) if total_tokens_values else 0,
                "avg_total_tokens": (sum(total_tokens_values) / len(total_tokens_values)) if total_tokens_values else None,
            }

            all_results["flows"][flow_name][dataset_name] = {
                "summary": summary,
                "cases": results,
            }

    try:
        await runner.cleanup()
    except Exception as e:  # pragma: no cover - cleanup errors ignored
        print(f"Warning: failed to cleanup flow runner: {e}")

    if args.output:
        Path(args.output).write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

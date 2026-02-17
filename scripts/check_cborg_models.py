#!/usr/bin/env python3
"""Utility to inspect available CBORG model IDs via /v1/models."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any


def _request_json(url: str, api_key: str, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, headers=headers, method=method, data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def fetch_model_ids(base_url: str, api_key: str) -> list[str]:
    base = base_url.rstrip("/")
    payload = _request_json(f"{base}/v1/models", api_key)
    data = payload.get("data", [])
    ids = [item.get("id") for item in data if isinstance(item, dict) and item.get("id")]
    return sorted(set(ids))


def try_chat_completion(
    base_url: str, api_key: str, model_id: str, max_tokens: int = 16
) -> tuple[bool, str]:
    base = base_url.rstrip("/")
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": max_tokens,
    }
    try:
        _request_json(f"{base}/chat/completions", api_key, method="POST", payload=payload)
        return True, "ok"
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""
        return False, f"HTTP {exc.code}: {error_body.strip()}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)


def model_ids_from_config(config_path: str) -> list[str]:
    """Extract model IDs from the top-level ``models:`` section of a config YAML."""
    with open(config_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    in_models = False
    found: list[str] = []
    pattern = re.compile(r"^\s*model_id:\s*(.+?)\s*$")

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not in_models:
            if re.match(r"^models:\s*$", stripped):
                in_models = True
            continue

        # Stop when we leave the top-level models block.
        if not line.startswith((" ", "\t")) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", stripped):
            break

        match = pattern.match(line)
        if not match:
            continue

        value = match.group(1).strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        found.append(value)

    # Keep order stable while deduplicating.
    unique: list[str] = []
    seen: set[str] = set()
    for model_id in found:
        if model_id not in seen:
            seen.add(model_id)
            unique.append(model_id)
    return unique


def resolve_catalog_model_id(config_model_id: str, catalog_ids: set[str]) -> tuple[bool, str]:
    """Resolve a configured model ID against catalog IDs, allowing simple provider-prefix aliases."""
    if config_model_id in catalog_ids:
        return True, config_model_id
    if "/" in config_model_id:
        alias = config_model_id.split("/", 1)[1]
        if alias in catalog_ids:
            return True, alias
    return False, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CBORG models exposed by /v1/models")
    parser.add_argument(
        "--base-url",
        default=os.getenv("CBORG_API_URL", "https://api.cborg.lbl.gov"),
        help="CBORG API base URL (default: $CBORG_API_URL or https://api.cborg.lbl.gov)",
    )
    parser.add_argument(
        "--api-key-env",
        default="CBORG_API_KEY",
        help="Environment variable name containing the API key (default: CBORG_API_KEY)",
    )
    parser.add_argument(
        "--contains",
        action="append",
        default=[],
        help="Filter listed models to those containing this substring (repeatable)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print model IDs. Default is summary/check output only.",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Exact model ID to verify exists (repeatable). Exits nonzero if missing.",
    )
    parser.add_argument(
        "--from-config",
        default=None,
        help="Read model IDs from config YAML (e.g. config/config.yaml).",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check every model ID found via --from-config.",
    )
    parser.add_argument(
        "--chat-test",
        action="append",
        default=[],
        help="Attempt a tiny /chat/completions call for this model ID (repeatable)",
    )
    parser.add_argument(
        "--chat-max-tokens",
        type=int,
        default=16,
        help="max_tokens for chat smoke tests (default: 16)",
    )
    parser.add_argument(
        "--chat-test-all",
        action="store_true",
        help="Run chat smoke test for every model ID found via --from-config.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print matching model IDs (suppresses summary lines)",
    )
    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        print(f"ERROR: {args.api_key_env} is not set", file=sys.stderr)
        return 2

    config_model_ids: list[str] = []
    if args.from_config:
        try:
            config_model_ids = model_ids_from_config(args.from_config)
        except Exception as exc:
            print(f"ERROR: failed to parse config {args.from_config}: {exc}", file=sys.stderr)
            return 2
        if not config_model_ids:
            print(f"ERROR: no model_id entries found in {args.from_config}", file=sys.stderr)
            return 2

        # Default behavior for --from-config is to check all configured models.
        if not (args.check_all or args.chat_test_all or args.check or args.chat_test):
            args.check_all = True

    try:
        model_ids = fetch_model_ids(args.base_url, api_key)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(
            f"ERROR: HTTP {exc.code} calling {args.base_url.rstrip('/')}/v1/models",
            file=sys.stderr,
        )
        print(body, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: failed to fetch models: {exc}", file=sys.stderr)
        return 1

    should_list = args.list or bool(args.contains)
    filtered = model_ids
    for pattern in args.contains:
        filtered = [m for m in filtered if pattern in m]

    if not args.quiet:
        shown = len(filtered) if should_list else 0
        print(
            f"base_url={args.base_url.rstrip('/')} model_count={len(model_ids)} shown={shown}"
        )

    if should_list:
        for model_id in filtered:
            print(model_id)

    check_targets = list(args.check)
    if args.check_all:
        if not args.from_config:
            print("ERROR: --check-all requires --from-config", file=sys.stderr)
            return 2
        for model_id in config_model_ids:
            if model_id not in check_targets:
                check_targets.append(model_id)

    missing: list[str] = []
    catalog_set = set(model_ids)
    if check_targets:
        for model_id in check_targets:
            ok, matched = resolve_catalog_model_id(model_id, catalog_set)
            if ok:
                if matched != model_id:
                    print(f"CHECK OK      {model_id} (catalog alias: {matched})")
                else:
                    print(f"CHECK OK      {model_id}")
            else:
                print(f"CHECK MISSING {model_id}")
                missing.append(model_id)

    chat_targets = list(args.chat_test)
    if args.chat_test_all:
        if not args.from_config:
            print("ERROR: --chat-test-all requires --from-config", file=sys.stderr)
            return 2
        for model_id in config_model_ids:
            if model_id not in chat_targets:
                chat_targets.append(model_id)

    chat_failures: list[str] = []
    if chat_targets:
        for model_id in chat_targets:
            ok, detail = try_chat_completion(
                args.base_url, api_key, model_id, max_tokens=args.chat_max_tokens
            )
            status = "CHAT OK" if ok else "CHAT FAIL"
            print(f"{status:<9} {model_id} :: {detail}")
            if not ok:
                chat_failures.append(model_id)

    if missing and chat_failures:
        return 5
    if chat_failures:
        return 4
    if missing:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

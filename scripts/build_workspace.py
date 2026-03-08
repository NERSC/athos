#!/usr/bin/env python3
"""Assemble/update workspace data from latest snapshots under ./data.

This script picks:
- the latest ServiceNow ticket snapshot directory under ``data/``
- the latest aggregate Chroma persist directory under ``data/chroma/aggregates/``
  (falls back to any Chroma DB under ``data/chroma/`` if no aggregate exists)

Then it replaces:
- ``<workspace>/servicenow_incidents``
- ``<workspace>/chroma``
- ``<workspace>/docs``
- ``<workspace>/consulting_docs``

with copies of those selected sources.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Iterable


DATE_RE = re.compile(r"(20\d{6})")


def _extract_latest_date_token(name: str) -> int:
    """Return YYYYMMDD token found in name, or 0 when absent."""
    matches = DATE_RE.findall(name)
    if not matches:
        return 0
    return max(int(token) for token in matches)


def _tickets_variant_priority(name: str) -> int:
    """Prefer filtered snapshots when date ties.

    Higher values are preferred.
    """
    lowered = name.lower()
    if "_filtered" in lowered:
        return 3
    if "_retrieval_lt_" in lowered:
        return 2
    if "_candidate_ge_" in lowered:
        return 1
    return 0


def _chroma_variant_priority(name: str) -> int:
    """Prefer ticket corpora over docs corpora when date ties.

    Higher values are preferred.
    """
    lowered = name.lower()
    if "servicenow_tickets" in lowered:
        return 2
    if "docs" in lowered:
        return 1
    return 0


def _select_latest(
    candidates: Iterable[Path],
    *,
    variant_priority,
    preferred_date: int | None = None,
) -> Path:
    available = [p for p in candidates if p.is_dir()]
    if not available:
        raise FileNotFoundError("No matching directories found.")

    if preferred_date is not None:
        preferred = [
            p for p in available if _extract_latest_date_token(p.name) == preferred_date
        ]
        if preferred:
            available = preferred

    def key(path: Path) -> tuple[int, int, float, str]:
        return (
            _extract_latest_date_token(path.name),
            variant_priority(path.name),
            path.stat().st_mtime,
            path.name,
        )

    return max(available, key=key)


def _replace_tree(source: Path, target: Path, dry_run: bool) -> None:
    if dry_run:
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, symlinks=True)


def _dir_signature(root: Path) -> str:
    """Return a stable signature for directory content + metadata."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        stat = path.lstat()
        if path.is_symlink():
            marker = f"L|{rel}|{path.readlink().as_posix()}"
        elif path.is_dir():
            marker = f"D|{rel}"
        else:
            marker = f"F|{rel}|{stat.st_size}|{int(stat.st_mtime_ns)}"
        digest.update(marker.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _sync_component(
    source: Path,
    target: Path,
    *,
    dry_run: bool,
    skip_unchanged: bool,
) -> str:
    """Sync one component and return action: copied/skipped."""
    if skip_unchanged and target.exists():
        if _dir_signature(source) == _dir_signature(target):
            return "skipped"
    _replace_tree(source, target, dry_run=dry_run)
    return "copied"


def _discover_ticket_candidates(data_dir: Path) -> list[Path]:
    # Consider top-level versioned snapshots only.
    return sorted(
        p
        for p in data_dir.iterdir()
        if p.is_dir()
        and p.name.startswith("servicenow_tickets_")
        and p.name != "servicenow_incidents"
    )


def _discover_chroma_candidates(chroma_root: Path) -> list[Path]:
    if not chroma_root.exists():
        return []

    candidates: list[Path] = []
    aggregate_root = chroma_root / "aggregates"

    # Default to aggregate DB snapshots when available.
    if aggregate_root.exists():
        for path in aggregate_root.rglob("chroma.sqlite3"):
            parent = path.parent
            if parent not in candidates:
                candidates.append(parent)
        if candidates:
            return sorted(candidates)

    # Fallback: any Chroma DB under data/chroma.
    for path in chroma_root.rglob("chroma.sqlite3"):
        parent = path.parent
        if parent not in candidates:
            candidates.append(parent)
    return sorted(candidates)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble/update ATHOS workspace from latest data snapshots "
            "(tickets + Chroma DB + docs + consulting_docs)."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Root data directory containing ticket snapshots and chroma/",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("workspace"),
        help="Workspace root directory to update",
    )
    parser.add_argument(
        "--tickets-dir",
        type=Path,
        default=None,
        help="Explicit ticket source directory (skips auto-select)",
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=None,
        help="Explicit Chroma source directory containing chroma.sqlite3 (skips auto-select)",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help="Explicit docs source directory (default: <data-dir>/docs)",
    )
    parser.add_argument(
        "--consulting-docs-dir",
        type=Path,
        default=None,
        help="Explicit consulting docs source directory (default: <data-dir>/consulting_docs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected sources and targets without copying",
    )
    parser.add_argument(
        "-s",
        "--skip",
        "--skip-unchanged",
        dest="skip_unchanged",
        action="store_true",
        help="Skip replacing a target directory when source and target are unchanged",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Optional manifest output path (default: <workspace>/.workspace_assembly_manifest.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data_dir = args.data_dir.resolve()
    workspace_dir = args.workspace_dir.resolve()

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if args.tickets_dir is not None:
        tickets_src = args.tickets_dir.resolve()
        if not tickets_src.is_dir():
            raise FileNotFoundError(f"Ticket source directory not found: {tickets_src}")
    else:
        ticket_candidates = _discover_ticket_candidates(data_dir)
        tickets_src = _select_latest(
            ticket_candidates,
            variant_priority=_tickets_variant_priority,
        )

    tickets_date = _extract_latest_date_token(tickets_src.name)

    chroma_root = data_dir / "chroma"
    if args.chroma_dir is not None:
        chroma_src = args.chroma_dir.resolve()
        if not (chroma_src / "chroma.sqlite3").exists():
            raise FileNotFoundError(
                f"Chroma source must contain chroma.sqlite3: {chroma_src}"
            )
    else:
        chroma_candidates = _discover_chroma_candidates(chroma_root)
        chroma_src = _select_latest(
            chroma_candidates,
            variant_priority=_chroma_variant_priority,
            preferred_date=tickets_date if tickets_date else None,
        )

    if args.docs_dir is not None:
        docs_src = args.docs_dir.resolve()
    else:
        docs_src = (data_dir / "docs").resolve()
    if not docs_src.is_dir():
        raise FileNotFoundError(f"Docs source directory not found: {docs_src}")

    if args.consulting_docs_dir is not None:
        consulting_docs_src = args.consulting_docs_dir.resolve()
    else:
        consulting_docs_src = (data_dir / "consulting_docs").resolve()
    if not consulting_docs_src.is_dir():
        raise FileNotFoundError(
            f"Consulting docs source directory not found: {consulting_docs_src}"
        )

    tickets_dst = workspace_dir / "servicenow_incidents"
    chroma_dst = workspace_dir / "chroma"
    docs_dst = workspace_dir / "docs"
    consulting_docs_dst = workspace_dir / "consulting_docs"

    if not args.dry_run:
        workspace_dir.mkdir(parents=True, exist_ok=True)

    tickets_action = _sync_component(
        tickets_src,
        tickets_dst,
        dry_run=args.dry_run,
        skip_unchanged=args.skip_unchanged,
    )
    chroma_action = _sync_component(
        chroma_src,
        chroma_dst,
        dry_run=args.dry_run,
        skip_unchanged=args.skip_unchanged,
    )
    docs_action = _sync_component(
        docs_src,
        docs_dst,
        dry_run=args.dry_run,
        skip_unchanged=args.skip_unchanged,
    )
    consulting_docs_action = _sync_component(
        consulting_docs_src,
        consulting_docs_dst,
        dry_run=args.dry_run,
        skip_unchanged=args.skip_unchanged,
    )

    manifest_path = (
        args.manifest_path.resolve()
        if args.manifest_path is not None
        else workspace_dir / ".workspace_assembly_manifest.json"
    )
    manifest = {
        "assembled_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "data_dir": str(data_dir),
        "workspace_dir": str(workspace_dir),
        "tickets_source": str(tickets_src),
        "tickets_target": str(tickets_dst),
        "tickets_action": tickets_action,
        "chroma_source": str(chroma_src),
        "chroma_target": str(chroma_dst),
        "chroma_action": chroma_action,
        "docs_source": str(docs_src),
        "docs_target": str(docs_dst),
        "docs_action": docs_action,
        "consulting_docs_source": str(consulting_docs_src),
        "consulting_docs_target": str(consulting_docs_dst),
        "consulting_docs_action": consulting_docs_action,
    }

    if not args.dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"tickets_source={tickets_src}")
    print(f"tickets_target={tickets_dst}")
    print(f"tickets_action={tickets_action}")
    print(f"chroma_source={chroma_src}")
    print(f"chroma_target={chroma_dst}")
    print(f"chroma_action={chroma_action}")
    print(f"docs_source={docs_src}")
    print(f"docs_target={docs_dst}")
    print(f"docs_action={docs_action}")
    print(f"consulting_docs_source={consulting_docs_src}")
    print(f"consulting_docs_target={consulting_docs_dst}")
    print(f"consulting_docs_action={consulting_docs_action}")
    print(f"dry_run={args.dry_run}")
    if not args.dry_run:
        print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()

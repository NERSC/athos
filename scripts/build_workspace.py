#!/usr/bin/env python3
"""Assemble/update explicit workspace assets and filesystem-eval bundle content.

Each copied component is opt-in via its path argument:
- ``--tickets-dir`` -> ``<workspace>/servicenow_incidents``
- ``--chroma-dir`` -> ``<workspace>/chroma``
- ``--docs-dir`` -> ``<workspace>/docs``
- ``--consulting-docs-dir`` -> ``<workspace>/consulting_docs``
- ``--fs-*-dir`` -> ``<workspace>/file_retrieval_corpus/...``

When any ``--fs-*-dir`` path is provided, the filesystem retrieval corpus is created
or updated automatically. ``--build-fs-index`` controls whether the bundle
receives a generated ``INDEX.md``. ``manifest.json`` is always written for the
bundle when bundle content is requested.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def _replace_tree(source: Path, target: Path, dry_run: bool) -> None:
    if dry_run:
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, symlinks=True)


def _write_text(path: Path, content: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _build_file_retrieval_corpus(
    *,
    bundle_dir: Path,
    docs_src: Path,
    consulting_docs_src: Path,
    dry_run: bool,
    skip_unchanged: bool,
    include_tickets: bool,
    tickets_src: Path | None,
    build_index: bool,
) -> dict[str, object]:
    docs_dst = bundle_dir / "docs"
    consulting_docs_dst = bundle_dir / "consulting_docs"

    if not dry_run:
        bundle_dir.mkdir(parents=True, exist_ok=True)

    docs_action = _sync_component(
        docs_src,
        docs_dst,
        dry_run=dry_run,
        skip_unchanged=skip_unchanged,
    )
    consulting_docs_action = _sync_component(
        consulting_docs_src,
        consulting_docs_dst,
        dry_run=dry_run,
        skip_unchanged=skip_unchanged,
    )

    tickets_action = "not_included"
    tickets_dst: Path | None = None
    if include_tickets:
        if tickets_src is None:
            raise ValueError("tickets_src is required when include_tickets=True")
        tickets_dst = bundle_dir / "tickets"
        tickets_action = _sync_component(
            tickets_src,
            tickets_dst,
            dry_run=dry_run,
            skip_unchanged=skip_unchanged,
        )

    bundle_manifest = {
        "schema_version": "athos.file_retrieval_corpus.v0",
        "bundle_dir": str(bundle_dir),
        "docs_source": str(docs_src),
        "docs_target": str(docs_dst),
        "docs_action": docs_action,
        "consulting_docs_source": str(consulting_docs_src),
        "consulting_docs_target": str(consulting_docs_dst),
        "consulting_docs_action": consulting_docs_action,
        "tickets_included": include_tickets,
        "tickets_source": str(tickets_src) if tickets_src is not None else None,
        "tickets_target": str(tickets_dst) if tickets_dst is not None else None,
        "tickets_action": tickets_action,
        "index_generated": build_index,
    }

    if build_index:
        index_lines = [
            "# File Retrieval Corpus",
            "",
            "This corpus is a narrowed subtree for filesystem-tool evaluation.",
            "",
            "## Contents",
            "",
            f"- `docs/`: copied from `{docs_src}`",
            f"- `consulting_docs/`: copied from `{consulting_docs_src}`",
        ]
        if include_tickets and tickets_src is not None:
            index_lines.append(f"- `tickets/`: copied from `{tickets_src}`")
        else:
            index_lines.append("- `tickets/`: not included in this bundle build")
        index_lines.extend(
            [
                "",
                "## Required Starting Point",
                "",
                "- Read this `INDEX.md` first.",
                "- Use the topic map below to pick one likely location before broader searching.",
                "- Prefer reading a specific file over repeated broad searches.",
                "",
                "## Topic Map",
                "",
                "### QOS, queue, walltime, charging, premium/debug limits",
                "",
                "- Start with `docs/jobs/policy.md`.",
                "- If the question is about how to run or monitor jobs on Perlmutter, then also check `docs/systems/perlmutter/running-jobs/index.md`.",
                "",
                "### Slurm job scripts, #SBATCH flags, MPI/OpenMP, srun options",
                "",
                "- Start with `docs/jobs/examples/index.md` for job script examples and `#SBATCH` flag usage.",
                "- For job policy, limits, and QOS details, also check `docs/jobs/policy.md`.",
                "",
                "### Perlmutter system hardware, CPU/GPU node details",
                "",
                "- Start with `docs/systems/perlmutter/architecture.md`.",
                "- For GPU questions, also inspect `docs/systems/perlmutter/` and nearby files under that directory.",
                "",
                "### Filesystem policy, purge rules, scratch/home/CFS",
                "",
                "- Start with files under `docs/filesystems/`.",
                "- For purge-policy questions, check `docs/filesystems/perlmutter-scratch.md` first.",
                "",
                "### AI software support and consulting guidance",
                "",
                "- Start by searching under `consulting_docs/` for `AI`, `ML`, `support`, or the topic named in the question.",
                "- If the question is about a NERSC support group or internal consulting practice, prefer `consulting_docs/` over `docs/`.",
                "",
                "### Historical tickets and past incident examples",
                "",
            ]
        )
        if include_tickets and tickets_src is not None:
            index_lines.extend(
                [
                    "- Start within `tickets/` when the question is about a past incident, workaround, or troubleshooting history.",
                    "- Search using a specific incident id, product name, filesystem name, or error string.",
                    "- Ticket records are stored as per-ticket files; prefer a narrow search first, then read only the most relevant matching file.",
                    "- If the question is policy or documentation oriented rather than incident-history oriented, prefer `docs/` or `consulting_docs/` first.",
                    "",
                ]
            )
        else:
            index_lines.extend(
                [
                    "- `tickets/` is not included in this build, so answer from `docs/` and `consulting_docs/` only.",
                    "",
                ]
            )
        index_lines.extend(
            [
                "### General search fallback",
                "",
                "- If the topic map does not clearly apply, do one narrow search within either `docs/` or `consulting_docs/`.",
                "- If `tickets/` is included and the question explicitly sounds incident- or workaround-oriented, do one narrow search within `tickets/` instead.",
                "- Avoid repeating the same broad search across the entire bundle with only minor wording changes.",
                "",
                "## Mini QA Routing Hints",
                "",
                "- `perlmutter_debug_qos`: start with `docs/jobs/policy.md`.",
                "- `premium_qos_charge_factor`: start with `docs/jobs/policy.md`.",
                "- `perlmutter_gpus`: start with `docs/systems/perlmutter/architecture.md`.",
                "- `purged_filesystem`: start with `docs/filesystems/perlmutter-scratch.md`.",
                "- `nersc_ai_support_group`: start by searching under `consulting_docs/` for `AI support` or `AI software`.",
                "",
                "See `manifest.json` for provenance.",
                "",
            ]
        )

        _write_text(bundle_dir / "INDEX.md", "\n".join(index_lines), dry_run=dry_run)
    _write_text(
        bundle_dir / "manifest.json",
        json.dumps(bundle_manifest, indent=2) + "\n",
        dry_run=dry_run,
    )

    return bundle_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble/update ATHOS workspace from explicit source paths."
        )
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
        help="Ticket source directory to copy into <workspace>/servicenow_incidents",
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=None,
        help="Chroma source directory containing chroma.sqlite3 to copy into <workspace>/chroma",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help="Docs source directory to copy into <workspace>/docs",
    )
    parser.add_argument(
        "--consulting-docs-dir",
        type=Path,
        default=None,
        help="Consulting docs source directory to copy into <workspace>/consulting_docs",
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
    parser.add_argument(
        "--build-fs-index",
        action="store_true",
        help="Generate INDEX.md for <workspace>/file_retrieval_corpus when any --fs-*-dir is provided.",
    )
    parser.add_argument(
        "--fs-bundle-subdir",
        default="file_retrieval_corpus",
        help="Subdirectory name under the workspace for the filesystem-eval bundle.",
    )
    parser.add_argument(
        "--fs-docs-dir",
        type=Path,
        default=None,
        help="Explicit docs source directory for the filesystem-eval bundle only.",
    )
    parser.add_argument(
        "--fs-consulting-docs-dir",
        type=Path,
        default=None,
        help="Explicit consulting docs source directory for the filesystem-eval bundle only.",
    )
    parser.add_argument(
        "--fs-tickets-dir",
        type=Path,
        default=None,
        help="Explicit ticket source directory for the filesystem-eval bundle only.",
    )
    parser.add_argument(
        "--fs-include-tickets",
        action="store_true",
        help="Include the selected ticket corpus under <fs-bundle>/tickets.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    workspace_dir = args.workspace_dir.resolve()

    tickets_dst = workspace_dir / "servicenow_incidents"
    chroma_dst = workspace_dir / "chroma"
    docs_dst = workspace_dir / "docs"
    consulting_docs_dst = workspace_dir / "consulting_docs"

    if not args.dry_run:
        workspace_dir.mkdir(parents=True, exist_ok=True)

    tickets_src = args.tickets_dir.resolve() if args.tickets_dir is not None else None
    if tickets_src is not None and not tickets_src.is_dir():
        raise FileNotFoundError(f"Ticket source directory not found: {tickets_src}")
    if tickets_src is not None:
        tickets_action = _sync_component(
            tickets_src,
            tickets_dst,
            dry_run=args.dry_run,
            skip_unchanged=args.skip_unchanged,
        )
    else:
        tickets_action = "not_requested"

    chroma_src = args.chroma_dir.resolve() if args.chroma_dir is not None else None
    if chroma_src is not None and not (chroma_src / "chroma.sqlite3").exists():
        raise FileNotFoundError(
            f"Chroma source must contain chroma.sqlite3: {chroma_src}"
        )
    if chroma_src is not None:
        chroma_action = _sync_component(
            chroma_src,
            chroma_dst,
            dry_run=args.dry_run,
            skip_unchanged=args.skip_unchanged,
        )
    else:
        chroma_action = "not_requested"

    docs_src = args.docs_dir.resolve() if args.docs_dir is not None else None
    if docs_src is not None and not docs_src.is_dir():
        raise FileNotFoundError(f"Docs source directory not found: {docs_src}")
    if docs_src is not None:
        docs_action = _sync_component(
            docs_src,
            docs_dst,
            dry_run=args.dry_run,
            skip_unchanged=args.skip_unchanged,
        )
    else:
        docs_action = "not_requested"

    consulting_docs_src = (
        args.consulting_docs_dir.resolve()
        if args.consulting_docs_dir is not None
        else None
    )
    if consulting_docs_src is not None and not consulting_docs_src.is_dir():
        raise FileNotFoundError(
            f"Consulting docs source directory not found: {consulting_docs_src}"
        )
    if consulting_docs_src is not None:
        consulting_docs_action = _sync_component(
            consulting_docs_src,
            consulting_docs_dst,
            dry_run=args.dry_run,
            skip_unchanged=args.skip_unchanged,
        )
    else:
        consulting_docs_action = "not_requested"

    file_retrieval_corpus_manifest: dict[str, object] | None = None
    if (
        args.fs_docs_dir is not None
        or args.fs_consulting_docs_dir is not None
        or args.fs_tickets_dir is not None
    ):
        fs_bundle_dir = workspace_dir / args.fs_bundle_subdir
        if args.fs_docs_dir is None or args.fs_consulting_docs_dir is None:
            raise FileNotFoundError(
                "Filesystem-eval bundle requires both --fs-docs-dir and "
                "--fs-consulting-docs-dir."
            )
        fs_docs_src = args.fs_docs_dir.resolve()
        if not fs_docs_src.is_dir():
            raise FileNotFoundError(
                f"Filesystem-eval docs source directory not found: {fs_docs_src}"
            )
        fs_consulting_docs_src = args.fs_consulting_docs_dir.resolve()
        if not fs_consulting_docs_src.is_dir():
            raise FileNotFoundError(
                "Filesystem-eval consulting docs source directory not found: "
                f"{fs_consulting_docs_src}"
            )
        fs_tickets_src = args.fs_tickets_dir.resolve() if args.fs_tickets_dir is not None else None
        if args.fs_include_tickets and (
            fs_tickets_src is None or not fs_tickets_src.is_dir()
        ):
            raise FileNotFoundError(
                "Filesystem-eval ticket source directory not found: "
                f"{fs_tickets_src}"
            )
        file_retrieval_corpus_manifest = _build_file_retrieval_corpus(
            bundle_dir=fs_bundle_dir,
            docs_src=fs_docs_src,
            consulting_docs_src=fs_consulting_docs_src,
            dry_run=args.dry_run,
            skip_unchanged=args.skip_unchanged,
            include_tickets=args.fs_include_tickets,
            tickets_src=fs_tickets_src,
            build_index=args.build_fs_index,
        )

    manifest_path = (
        args.manifest_path.resolve()
        if args.manifest_path is not None
        else workspace_dir / ".workspace_assembly_manifest.json"
    )
    manifest = {
        "assembled_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "workspace_dir": str(workspace_dir),
        "tickets_source": str(tickets_src) if tickets_src is not None else None,
        "tickets_target": str(tickets_dst) if tickets_src is not None else None,
        "tickets_action": tickets_action,
        "chroma_source": str(chroma_src) if chroma_src is not None else None,
        "chroma_target": str(chroma_dst) if chroma_src is not None else None,
        "chroma_action": chroma_action,
        "docs_source": str(docs_src) if docs_src is not None else None,
        "docs_target": str(docs_dst) if docs_src is not None else None,
        "docs_action": docs_action,
        "consulting_docs_source": (
            str(consulting_docs_src) if consulting_docs_src is not None else None
        ),
        "consulting_docs_target": (
            str(consulting_docs_dst) if consulting_docs_src is not None else None
        ),
        "consulting_docs_action": consulting_docs_action,
        "file_retrieval_corpus": file_retrieval_corpus_manifest,
    }

    if not args.dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"tickets_source={tickets_src}")
    print(f"tickets_target={tickets_dst if tickets_src is not None else None}")
    print(f"tickets_action={tickets_action}")
    print(f"chroma_source={chroma_src}")
    print(f"chroma_target={chroma_dst if chroma_src is not None else None}")
    print(f"chroma_action={chroma_action}")
    print(f"docs_source={docs_src}")
    print(f"docs_target={docs_dst if docs_src is not None else None}")
    print(f"docs_action={docs_action}")
    print(f"consulting_docs_source={consulting_docs_src}")
    print(
        "consulting_docs_target="
        f"{consulting_docs_dst if consulting_docs_src is not None else None}"
    )
    print(f"consulting_docs_action={consulting_docs_action}")
    if file_retrieval_corpus_manifest is not None:
        print(
            "file_retrieval_corpus_dir="
            f"{file_retrieval_corpus_manifest['bundle_dir']}"
        )
        print(
            "file_retrieval_corpus_docs_action="
            f"{file_retrieval_corpus_manifest['docs_action']}"
        )
        print(
            "file_retrieval_corpus_consulting_docs_action="
            f"{file_retrieval_corpus_manifest['consulting_docs_action']}"
        )
        print(
            "file_retrieval_corpus_tickets_included="
            f"{file_retrieval_corpus_manifest['tickets_included']}"
        )
        print(
            "file_retrieval_corpus_tickets_action="
            f"{file_retrieval_corpus_manifest['tickets_action']}"
        )
    print(f"dry_run={args.dry_run}")
    if not args.dry_run:
        print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()

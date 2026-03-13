import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "build_workspace_mod",
    REPO_ROOT / "scripts" / "build_workspace.py",
)
build_workspace_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_workspace_mod)


def test_build_workspace_generates_docs_only_file_retrieval_corpus(
    tmp_path: Path, monkeypatch
):
    workspace_dir = tmp_path / "workspace"

    docs_src = tmp_path / "docs"
    (docs_src / "jobs").mkdir(parents=True)
    (docs_src / "jobs" / "qos.md").write_text("# QOS\n", encoding="utf-8")
    fs_docs_src = tmp_path / "docs_inner"
    (fs_docs_src / "slurm").mkdir(parents=True)
    (fs_docs_src / "slurm" / "debug.md").write_text("# Debug\n", encoding="utf-8")

    consulting_docs_src = tmp_path / "consulting_docs"
    (consulting_docs_src / "ai").mkdir(parents=True)
    (consulting_docs_src / "ai" / "support.md").write_text("# Support\n", encoding="utf-8")
    fs_consulting_docs_src = tmp_path / "consulting_docs_inner"
    (fs_consulting_docs_src / "playbooks").mkdir(parents=True)
    (fs_consulting_docs_src / "playbooks" / "ml.md").write_text("# ML\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_workspace.py",
            "--workspace-dir",
            str(workspace_dir),
            "--docs-dir",
            str(docs_src),
            "--consulting-docs-dir",
            str(consulting_docs_src),
            "--fs-docs-dir",
            str(fs_docs_src),
            "--fs-consulting-docs-dir",
            str(fs_consulting_docs_src),
            "--build-fs-index",
        ],
    )

    build_workspace_mod.main()

    assert (workspace_dir / "docs" / "jobs" / "qos.md").exists()
    assert (workspace_dir / "consulting_docs" / "ai" / "support.md").exists()
    assert not (workspace_dir / "servicenow_incidents").exists()

    bundle_dir = workspace_dir / "file_retrieval_corpus"
    assert (bundle_dir / "docs" / "slurm" / "debug.md").exists()
    assert (bundle_dir / "consulting_docs" / "playbooks" / "ml.md").exists()
    assert not (bundle_dir / "docs" / "jobs" / "qos.md").exists()
    assert not (bundle_dir / "consulting_docs" / "ai" / "support.md").exists()
    assert not (bundle_dir / "tickets").exists()

    index_text = (bundle_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "Filesystem Eval Bundle" in index_text
    assert "`tickets/`: not included" in index_text

    bundle_manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert bundle_manifest["schema_version"] == "athos.file_retrieval_corpus.v0"
    assert bundle_manifest["tickets_included"] is False
    assert bundle_manifest["tickets_action"] == "not_included"
    assert bundle_manifest["index_generated"] is True
    assert bundle_manifest["docs_source"] == str(fs_docs_src)
    assert bundle_manifest["consulting_docs_source"] == str(fs_consulting_docs_src)

    workspace_manifest = json.loads(
        (workspace_dir / ".workspace_assembly_manifest.json").read_text(encoding="utf-8")
    )
    assert workspace_manifest["tickets_action"] == "not_requested"
    assert workspace_manifest["file_retrieval_corpus"]["bundle_dir"] == str(bundle_dir)
    assert workspace_manifest["file_retrieval_corpus"]["docs_action"] == "copied"


def test_build_workspace_generates_ticket_inclusive_file_retrieval_corpus(
    tmp_path: Path, monkeypatch
):
    workspace_dir = tmp_path / "workspace"

    tickets_src = tmp_path / "servicenow_tickets_20260310_filtered"
    (tickets_src / "INC001" / "01").mkdir(parents=True)
    (tickets_src / "INC001" / "01" / "retrieval.json").write_text("{}", encoding="utf-8")

    docs_src = tmp_path / "docs"
    (docs_src / "jobs").mkdir(parents=True)
    (docs_src / "jobs" / "qos.md").write_text("# QOS\n", encoding="utf-8")

    consulting_docs_src = tmp_path / "consulting_docs"
    (consulting_docs_src / "ai").mkdir(parents=True)
    (consulting_docs_src / "ai" / "support.md").write_text("# Support\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_workspace.py",
            "--workspace-dir",
            str(workspace_dir),
            "--docs-dir",
            str(docs_src),
            "--consulting-docs-dir",
            str(consulting_docs_src),
            "--fs-include-tickets",
            "--fs-docs-dir",
            str(docs_src),
            "--fs-consulting-docs-dir",
            str(consulting_docs_src),
            "--fs-tickets-dir",
            str(tickets_src),
            "--build-fs-index",
        ],
    )

    build_workspace_mod.main()

    bundle_dir = workspace_dir / "file_retrieval_corpus"
    assert (bundle_dir / "tickets" / "INC001" / "01" / "retrieval.json").exists()
    assert not (workspace_dir / "servicenow_incidents").exists()

    index_text = (bundle_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "`tickets/`: copied from" in index_text
    assert "Historical tickets and past incident examples" in index_text
    assert "stored as JSON" in index_text

    bundle_manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert bundle_manifest["tickets_included"] is True
    assert bundle_manifest["tickets_action"] == "copied"
    assert bundle_manifest["index_generated"] is True
    assert bundle_manifest["tickets_source"] == str(tickets_src)

from __future__ import annotations

from pathlib import Path

import pytest

from athos.utils.chroma_aggregate import AggregateSpecError, load_aggregate_spec


def test_load_aggregate_spec_parses_expected_fields(tmp_path: Path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        """
aggregate:
  name: test_bundle
  version: "20260225"
output:
  persist_dir: /tmp/test_bundle
  manifest_out: /tmp/test_bundle_manifest.json
  overwrite: false
components:
  - logical_name: docs
    source:
      persist_dir: /tmp/source_docs
      collection: docs_v1
      version: "1"
    target_collection: docs
validation:
  require_unique_target_collections: true
  fail_on_missing_collection: true
  fail_on_doc_count_zero: true
  batch_size: 250
""".strip()
    )

    spec = load_aggregate_spec(spec_path)

    assert spec.aggregate.name == "test_bundle"
    assert spec.aggregate.version == "20260225"
    assert spec.output.persist_dir == Path("/tmp/test_bundle")
    assert spec.validation.batch_size == 250
    assert len(spec.components) == 1
    assert spec.components[0].target_collection == "docs"


def test_load_aggregate_spec_rejects_duplicate_target_collection(tmp_path: Path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        """
aggregate:
  name: test_bundle
  version: "20260225"
output:
  persist_dir: /tmp/test_bundle
  manifest_out: /tmp/test_bundle_manifest.json
  overwrite: false
components:
  - logical_name: docs_a
    source:
      persist_dir: /tmp/source_a
      collection: docs_a
      version: "1"
    target_collection: docs
  - logical_name: docs_b
    source:
      persist_dir: /tmp/source_b
      collection: docs_b
      version: "1"
    target_collection: docs
validation:
  require_unique_target_collections: true
  fail_on_missing_collection: true
  fail_on_doc_count_zero: true
  batch_size: 100
""".strip()
    )

    with pytest.raises(AggregateSpecError, match="Duplicate target_collection"):
        load_aggregate_spec(spec_path)


def test_load_aggregate_spec_rejects_non_positive_batch_size(tmp_path: Path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        """
aggregate:
  name: test_bundle
  version: "20260225"
output:
  persist_dir: /tmp/test_bundle
  manifest_out: /tmp/test_bundle_manifest.json
  overwrite: false
components:
  - logical_name: docs
    source:
      persist_dir: /tmp/source_docs
      collection: docs_v1
      version: "1"
    target_collection: docs
validation:
  batch_size: 0
""".strip()
    )

    with pytest.raises(AggregateSpecError, match="batch_size must be > 0"):
        load_aggregate_spec(spec_path)

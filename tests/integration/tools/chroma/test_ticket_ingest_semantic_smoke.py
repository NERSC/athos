from __future__ import annotations

from pathlib import Path

import chromadb

from athos.utils.ticket_ingest import build_full_incident_document


def _toy_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic embedding function with simple synonym mapping."""
    vectors: list[list[float]] = []
    for text in texts:
        lower = text.lower()
        module_signal = any(
            phrase in lower
            for phrase in (
                "module",
                "import",
                "python package",
            )
        )
        quota_signal = any(
            phrase in lower
            for phrase in (
                "quota",
                "storage",
                "disk",
            )
        )
        vectors.append(
            [
                1.0 if module_signal else 0.0,
                1.0 if quota_signal else 0.0,
            ]
        )
    return vectors


def _record(incident_number: str, short_description: str, description: str) -> dict:
    return {
        "metadata": {
            "incident_number": incident_number,
            "sys_id": f"sys_{incident_number}",
        },
        "incident_fields": {
            "state": "Open",
            "category": "Software",
            "assignment_group": "Consulting",
            "sys_created_on": "2025-01-01 00:00:00",
            "sys_updated_on": "2025-01-01 01:00:00",
            "short_description": short_description,
            "description": description,
            "contact_type": "Email",
            "sys_created_by": "user",
        },
        "discussions": {
            "customer_facing_comments": [],
            "internal_work_notes": [],
        },
        "attachments": [],
    }


def test_ticket_ingest_smoke_keyword_and_semantic_query(tmp_path: Path):
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    collection = client.get_or_create_collection(name="ticket_smoke_semantic")

    records = [
        _record(
            "INC0001",
            "Module load fails for numpy",
            "User cannot import numpy in python environment",
        ),
        _record(
            "INC0002",
            "Quota warning on home directory",
            "Disk usage exceeded home storage allocation",
        ),
    ]

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    for idx, record in enumerate(records):
        docs = build_full_incident_document(record, Path(f"fixtures/ticket_{idx}.json"))
        assert len(docs) == 1
        ids.append(docs[0].doc_id)
        documents.append(docs[0].text)
        metadatas.append(docs[0].metadata)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=_toy_embed(documents),
    )

    keyword_result = collection.query(
        query_embeddings=_toy_embed(["numpy module load"]),
        n_results=1,
    )
    keyword_top_id = keyword_result["ids"][0][0]
    assert keyword_top_id.startswith("INC0001:full")

    semantic_result = collection.query(
        query_embeddings=_toy_embed(["python package import problem"]),
        n_results=1,
    )
    semantic_top_id = semantic_result["ids"][0][0]
    assert semantic_top_id.startswith("INC0001:full")

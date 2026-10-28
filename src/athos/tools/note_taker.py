"""Note tools for LangGraph agent flows, stored in a Chroma collection.

Each note is one record in the `consulting_notes` collection, with the note's
name as its id. The record's document (description, question and errors) is
what gets embedded for semantic search; its metadata holds `category`,
`status` and `confidence` and the full note as markdown under `note`. That
markdown has frontmatter with the searchable fields: `name`, a `description`
of when the note applies, `category`, `status`, `confidence`, and lists of
`tags`, exact `errors`, `job_ids`, `incidents` and `sources` (JSON arrays,
which are also valid YAML), and a body with the Question, Recommendation,
What was tried and Approach sections. Notes written before these fields
existed (with an Answer section) still load; they gain the new fields when
next updated.

- note_taker: save a new note or update an existing one.
- list_notes: find notes by meaning and by exact text, category, status or tag.
- read_note: load one note's markdown.
- take_thread_note: tell the front end the user wants the conversation
  noted. The Slack bot then hands the whole thread to a note-writer flow,
  which saves it with note_taker.

Generic, flow-agnostic tools: any flow can pick them up by adding their
names to its `tools:` list in config.yaml.

The Chroma database is $ATHOS_NOTES_CHROMA_DIR when set, else <notes
dir>/chroma, where the notes directory is $ATHOS_NOTES_DIR when set (point it
at persistent storage on the host, e.g. $ATHOS_WORKSPACE/notes in a
container), else <repo root>/.notes. Notes saved as <notes dir>/<name>/note.md
by earlier versions are imported the first time the collection is empty.

One client per process reads and writes the collection, so a note saved by
the note-writer flow is visible to the consulting flow running in the same
process (the Slack bot) right away. Chroma does not support several
processes writing one database: don't point chroma-mcp or a second bot at
this directory.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, get_args

import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

# src/athos/tools/note_taker.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]

Category = Literal[
    "job-failure",
    "job-submission",
    "qos-account",
    "modules-software",
    "filesystem-quota",
    "data-transfer",
    "performance",
    "licensing",
    "access-login",
    "other",
]
Status = Literal["resolved", "waiting-on-user", "needs-escalation"]
Confidence = Literal["high", "medium", "low"]
CATEGORIES = get_args(Category)
STATUSES = get_args(Status)
CONFIDENCES = get_args(Confidence)

_NOTE_FILE = "note.md"
_NAME_MAX = 64
_DESCRIPTION_MAX = 1024
_ITEM_MAX = 500
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
# "Answer" is the Recommendation heading of notes from before the structured format.
_SECTION_RE = re.compile(
    r"^## (Question|Recommendation|Answer|What was tried|Approach)[ \t]*$", re.MULTILINE
)
_LIST_FIELDS = ("tags", "errors", "job_ids", "incidents", "sources")
_NOTHING_TRIED = "Nothing recorded."
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by can could do does for from how i if in is it me my "
    "of on or should so that the there this to was what when where which who why "
    "will with would you your".split()
)
# A note matching a query by words alone must contain at least this share of
# its words: an exact error text, job ID or tag, not one shared word like "job".
_WORD_MATCH_MIN = 0.5
# Cosine distances with Chroma's default all-MiniLM-L6-v2 model: the same
# question reworded scores about 0.2-0.35, a related note up to about 0.6,
# and an unrelated one 0.7 or more.
_SIMILAR_DISTANCE = 0.4
_LISTED_DISTANCE = 0.65
_MAX_CANDIDATES = 3
_MAX_LISTED = 20
_COLLECTION = "consulting_notes"

_collections: Dict[str, Any] = {}
_collections_lock = threading.Lock()
# Serializes note_taker's check-then-save.
_write_lock = threading.Lock()


def _notes_dir() -> Path:
    configured = os.getenv("ATHOS_NOTES_DIR")
    return Path(configured) if configured else _REPO_ROOT / ".notes"


def _chroma_dir() -> Path:
    configured = os.getenv("ATHOS_NOTES_CHROMA_DIR")
    return Path(configured) if configured else _notes_dir() / "chroma"


def _embedding_function():
    return embedding_functions.DefaultEmbeddingFunction()


@dataclass
class _Note:
    name: str
    description: str
    question: str = ""
    recommendation: str = ""
    tried: str = ""
    approach: str = ""
    category: str = ""
    status: str = ""
    confidence: str = ""
    tags: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    job_ids: List[str] = field(default_factory=list)
    incidents: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    created: str = ""

    def search_text(self) -> str:
        return " ".join(
            [self.name, self.description, self.question, self.category]
            + self.tags + self.errors + self.job_ids + self.incidents
        )


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:_NAME_MAX].rstrip("-")


def _one_line(text: str, limit: int = _DESCRIPTION_MAX) -> str:
    return " ".join(text.split())[:limit]


def _clean_list(items: Optional[List[str]], *, slug: bool = False) -> List[str]:
    """One-line, non-empty, de-duplicated items (slugs for tags)."""
    cleaned: List[str] = []
    for item in items or []:
        value = _slugify(item) if slug else _one_line(str(item), _ITEM_MAX)
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned


def _parse_list(value: str) -> List[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [part.strip() for part in value.strip("[]").split(",") if part.strip()]
    return [str(item) for item in parsed] if isinstance(parsed, list) else [str(parsed)]


def _sections(body: str) -> dict[str, str]:
    """Split the body into its sections.

    Question is the first heading, Approach the last, so a heading-like line
    inside the recommendation (say, in a pasted file) cannot end it early.
    """
    matches = list(_SECTION_RE.finditer(body))
    question = next((m for m in matches if m.group(1) == "Question"), None)
    if question is None:
        return {}
    later = [m for m in matches if m.start() > question.start()]
    recommendation = next((m for m in later if m.group(1) in ("Recommendation", "Answer")), None)
    if recommendation is None:
        return {}
    approach = next(
        (m for m in reversed(later) if m.group(1) == "Approach" and m.start() > recommendation.start()),
        None,
    )
    end = approach.start() if approach else len(body)
    tried = next(
        (
            m
            for m in reversed(later)
            if m.group(1) == "What was tried" and recommendation.start() < m.start() < end
        ),
        None,
    )
    used = [
        (key, m)
        for key, m in (("question", question), ("recommendation", recommendation), ("tried", tried), ("approach", approach))
        if m
    ]
    ends = [m.start() for _, m in used[1:]] + [len(body)]
    return {key: body[m.end() : end].strip() for (key, m), end in zip(used, ends)}


def _parse(name: str, text: str) -> Optional[_Note]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    fields = dict(
        line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line
    )
    lists = {key: _parse_list(fields[key]) for key in _LIST_FIELDS if key in fields}
    sections = _sections(match.group(2))
    if sections.get("tried") == _NOTHING_TRIED:
        sections["tried"] = ""
    return _Note(
        name,
        fields.get("description", ""),
        category=fields.get("category", ""),
        status=fields.get("status", ""),
        confidence=fields.get("confidence", ""),
        created=fields.get("created", ""),
        **lists,
        **sections,
    )


def _load_markdown(root: Path) -> List[_Note]:
    """Notes saved as <root>/<name>/note.md by earlier versions."""
    if not root.is_dir():
        return []
    notes = []
    for folder in sorted(root.iterdir()):
        skill = folder / _NOTE_FILE
        if skill.is_file():
            note = _parse(folder.name, skill.read_text(encoding="utf-8"))
            if note:
                notes.append(note)
    return notes


def _render(note: _Note, now: str) -> str:
    lists = "".join(
        f"{key}: {json.dumps(getattr(note, key), ensure_ascii=False)}\n" for key in _LIST_FIELDS
    )
    return (
        "---\n"
        f"name: {note.name}\n"
        f"description: {_one_line(note.description)}\n"
        f"category: {note.category}\n"
        f"status: {note.status}\n"
        f"confidence: {note.confidence}\n"
        f"{lists}"
        f"created: {note.created or now}\n"
        f"updated: {now}\n"
        "---\n\n"
        f"## Question\n{note.question.strip()}\n\n"
        f"## Recommendation\n{note.recommendation.strip()}\n\n"
        f"## What was tried\n{note.tried.strip() or _NOTHING_TRIED}\n\n"
        f"## Approach\n{note.approach.strip()}\n"
    )


def _tokens(text: str) -> set[str]:
    return {
        token[:-1] if len(token) > 3 and token.endswith("s") else token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOPWORDS
    }


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _upsert(collection: Any, notes: List[_Note]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for note in notes:
        note.created = note.created or now
    collection.upsert(
        ids=[note.name for note in notes],
        documents=["\n".join([note.description, note.question, *note.errors]) for note in notes],
        metadatas=[
            {
                "category": note.category,
                "status": note.status,
                "confidence": note.confidence,
                "created": note.created,
                "updated": now,
                "note": _render(note, now),
            }
            for note in notes
        ],
    )


def _collection() -> Any:
    """This process's notes collection, created (and seeded from note.md files) on first use."""
    path = str(_chroma_dir())
    with _collections_lock:
        if path not in _collections:
            collection = chromadb.PersistentClient(path=path).get_or_create_collection(
                _COLLECTION,
                embedding_function=_embedding_function(),
                configuration={"hnsw": {"space": "cosine"}},
            )
            if collection.count() == 0:
                legacy = _load_markdown(_notes_dir())
                if legacy:
                    _upsert(collection, legacy)
            _collections[path] = collection
        return _collections[path]


def _load() -> List[_Note]:
    result = _collection().get(include=["metadatas"])
    notes = [
        _parse(name, (metadata or {}).get("note", ""))
        for name, metadata in zip(result["ids"], result["metadatas"])
    ]
    return sorted((note for note in notes if note), key=lambda note: note.name)


def _nearest(text: str, max_distance: float, limit: int) -> List[str]:
    """Names of the notes closest in meaning to `text`, nearest first."""
    collection = _collection()
    count = collection.count()
    if not count or not text.strip():
        return []
    result = collection.query(query_texts=[text], n_results=min(limit, count), include=["distances"])
    return [
        name
        for name, distance in zip(result["ids"][0], result["distances"][0])
        if distance <= max_distance
    ]


def _find_similar(question: str, notes: List[_Note]) -> List[_Note]:
    """Notes close enough in meaning that they may ask the same thing."""
    by_name = {note.name: note for note in notes}
    names = _nearest(question, _SIMILAR_DISTANCE, _MAX_CANDIDATES)
    return [by_name[name] for name in names if name in by_name]


def _labels(note: _Note) -> str:
    return " | ".join(value for value in (note.category, note.status, note.confidence) if value)


def _candidates_message(candidates: List[_Note]) -> str:
    lines = [
        "Similar note(s) already exist, so nothing was saved yet. Compare them with "
        "the current question and your recommendation, then call note_taker again "
        "with the same arguments plus one decision:",
        "- decision='update', note_name=N: note N asks the same thing, but your "
        "recommendation is more correct or complete. Your entry replaces it, so "
        "fold in anything from note N that is still correct (errors, job IDs, "
        "sources, what was tried).",
        "- decision='no_change', note_name=N: note N asks the same thing and is "
        "already correct and complete.",
        "- decision='new': none of these asks the same thing.",
    ]
    for note in candidates:
        lines += [
            "",
            f"[note_name={note.name}] {_labels(note)}",
            f"Description: {note.description}",
            f"Errors: {', '.join(note.errors) or 'none'}",
            f"Question: {note.question}",
            f"Recommendation: {note.recommendation}",
            f"What was tried: {note.tried}",
            f"Approach: {note.approach}",
        ]
    return "\n".join(lines)


@tool
def note_taker(
    name: str,
    description: str,
    category: Category,
    status: Status,
    confidence: Confidence,
    question: str,
    recommendation: str,
    approach: str,
    what_was_tried: str = "",
    tags: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    job_ids: Optional[List[str]] = None,
    incidents: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    decision: Optional[Literal["new", "update", "no_change"]] = None,
    note_name: Optional[str] = None,
) -> str:
    """Save a solved (or partly solved) support problem as a structured, reusable note.

    Each note is stored under its `name` in the notes database, where
    list_notes finds it from then on. Leave `decision` unset on the first call. If similar notes
    already exist, nothing is saved and they are shown to you; compare, then
    call again with a decision.

    Args:
        name: Short folder name for the note: lowercase words joined by
            hyphens, e.g. "perlmutter-gpus-per-node" (max 64 characters).
        description: One sentence saying what the note covers and when to use
            it. This is what list_notes shows later.
        category: The kind of problem: job-failure, job-submission,
            qos-account, modules-software, filesystem-quota, data-transfer,
            performance, licensing, access-login, or other.
        status: resolved, waiting-on-user (needs something from the user), or
            needs-escalation (needs staff action beyond consulting).
        confidence: high (confirmed by a source or the user), medium (well
            supported but unconfirmed), or low (a best guess).
        question: The problem, as one self-contained question.
        recommendation: The final recommendation, complete enough to act on.
        approach: How it was solved: what was missing, inputs that were
            needed but not available (e.g. job ID, Slurm output), where you
            looked, what you found, and the quickest route next time.
        what_was_tried: What the user or consultants already tried and what
            happened, one item per line.
        tags: Short lowercase search tags, e.g. ["perlmutter", "gpu", "sbatch"].
        errors: Exact error texts, verbatim, e.g. ["QOSMaxWallDurationPerJobLimit"].
        job_ids: Slurm job IDs mentioned.
        incidents: ServiceNow incident numbers, e.g. ["INC0012345"].
        sources: Sources cited: doc URLs or paths, Chroma collections and
            documents, incidents, saved note names.
        decision: Only on a follow-up call after similar notes were shown:
            'update' to replace note `note_name` with this entry, 'no_change'
            if note `note_name` is already correct, or 'new' to save a
            separate note.
        note_name: The existing note to update or keep, required with
            'update' and 'no_change'. An update keeps that note's name.

    Returns:
        What was saved, or the similar notes to compare against.
    """
    entry = _Note(
        "",
        description,
        question=question,
        recommendation=recommendation,
        tried=what_was_tried,
        approach=approach,
        category=category,
        status=status,
        confidence=confidence,
        tags=_clean_list(tags, slug=True),
        errors=_clean_list(errors),
        job_ids=_clean_list(job_ids),
        incidents=_clean_list(incidents),
        sources=_clean_list(sources),
    )
    collection = _collection()
    with _write_lock:
        notes = _load()
        names = {n.name: n for n in notes}

        if decision is None:
            candidates = _find_similar(question, notes)
            if candidates:
                return _candidates_message(candidates)
            decision = "new"

        if decision in ("update", "no_change"):
            if note_name not in names:
                return (
                    f"Error: decision='{decision}' needs note_name set to an "
                    "existing note shown to you. Call note_taker again with a "
                    "valid note_name."
                )
            if decision == "no_change":
                return (
                    f"No changes made; note '{note_name}' already covers this. "
                    "Now send your final answer to the user."
                )
            entry.name, entry.created = note_name, names[note_name].created
            _upsert(collection, [entry])
            return (
                f"Updated note '{note_name}'. Now send your final answer to the user."
            )

        slug = _slugify(name)
        if not slug:
            return (
                "Error: name must contain letters or digits. Call note_taker again "
                "with a short hyphenated name."
            )
        if slug in names:
            return (
                f"Error: a note named '{slug}' already exists. Call note_taker again "
                f"with decision='update', note_name='{slug}' if it asks the same "
                "thing, or with a different name."
            )
        entry.name = slug
        _upsert(collection, [entry])
        return f"Saved as note '{slug}'. Now send your final answer to the user."


@tool
def list_notes(
    query: str = "",
    category: Optional[Category] = None,
    status: Optional[Status] = None,
    tag: Optional[str] = None,
) -> str:
    """List saved notes from earlier support problems, closest in meaning first.

    Call this before answering, with the user's question (or an exact error
    text, job ID or incident number) as `query`, to find notes on the same
    or a related problem. Then call read_note with a matching name to load
    its recommendation and approach.

    Args:
        query: The question, or an exact error text, job ID or incident
            number. Matched by meaning against note descriptions, questions
            and errors, and by words against those plus names, tags, job IDs
            and incidents. Leave empty to list notes by name.
        category: Only notes in this category, e.g. "qos-account".
        status: Only notes with this status, e.g. "needs-escalation".
        tag: Only notes carrying this tag, e.g. "perlmutter".

    Returns:
        Matching notes as "- name [category | status | confidence]:
        description" lines.
    """
    notes = _load()
    if not notes:
        return "No notes saved yet."
    tag_slug = _slugify(tag or "")
    notes = [
        n
        for n in notes
        if (not category or n.category == category)
        and (not status or n.status == status)
        and (not tag_slug or tag_slug in n.tags)
    ]
    if query.strip():
        # Matches by meaning first, then notes that only share words.
        by_name = {n.name: n for n in notes}
        names = [name for name in _nearest(query, _LISTED_DISTANCE, _MAX_LISTED) if name in by_name]
        scored = [(_similarity(query, n.search_text()), n.name) for n in notes]
        scored = [item for item in scored if item[0] >= _WORD_MATCH_MIN and item[1] not in names]
        scored.sort(key=lambda item: item[0], reverse=True)
        notes = [by_name[name] for name in names + [name for _, name in scored]]
    if not notes:
        return "No notes match."
    shown = notes[:_MAX_LISTED]
    lines = [
        f"- {n.name}{f' [{_labels(n)}]' if _labels(n) else ''}: {n.description}" for n in shown
    ]
    if len(notes) > len(shown):
        lines.append(
            f"({len(notes) - len(shown)} more; use a more specific query to narrow.)"
        )
    lines.append("Call read_note with a name to load that note.")
    return "\n".join(lines)


@tool
def read_note(name: str) -> str:
    """Load one saved note: its fields, question, recommendation and approach.

    Use a note as a prior solution. If it asks the same thing and its
    recommendation fully resolves the user's question, answer from it;
    otherwise fall back to the other retrieval tools. Weigh its status and
    confidence: a low-confidence or unresolved note is a lead, not an answer.

    Args:
        name: The note's name, as shown by list_notes.

    Returns:
        The note's full text.
    """
    result = _collection().get(ids=[name], include=["metadatas"]) if _NAME_RE.match(name) else None
    if not result or not result["ids"]:
        return f"No note named '{name}'. Call list_notes to see available notes."
    return result["metadatas"][0]["note"]


@tool
def take_thread_note() -> str:
    """Ask the front end to save this whole conversation thread as a note.

    Call this, and nothing else, when the user asks you to note, take notes
    on, save or remember this conversation or thread, in any wording. The
    front end reads the full thread, summarizes it and saves the note, and
    replies to the user itself. Do not call it for questions about notes
    (e.g. how to take notes in Jupyter) or to look up saved notes.

    Returns:
        Confirmation that the request was passed on.
    """
    return "Thread note requested; the front end will save the thread and reply to the user."

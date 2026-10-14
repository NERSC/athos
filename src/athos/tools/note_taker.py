"""Note tools for LangGraph agent flows, stored as agent-style skills.

Each note is a folder under the notes directory holding one note.md:
frontmatter with a `name` and a `description` of when the note applies,
then the question, the answer and the approach that produced it.

- note_taker: save a new note or update an existing one.
- list_notes: find notes by name and description.
- read_note: load one note's note.md.
- take_thread_note: tell the front end the user wants the conversation
  noted. The Slack bot then hands the whole thread to a note-writer flow,
  which saves it with note_taker.

Generic, flow-agnostic tools: any flow can pick them up by adding their
names to its `tools:` list in config.yaml.

The notes directory is $ATHOS_NOTES_DIR when set (point it at persistent
storage on the host, e.g. $ATHOS_WORKSPACE/notes in a container), else
<repo root>/.notes.
"""

from __future__ import annotations

import fcntl
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Literal, Optional

from langchain_core.tools import tool

# src/athos/tools/note_taker.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]

_NOTE_FILE = "note.md"
_NAME_MAX = 64
_DESCRIPTION_MAX = 1024
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
# Answer is greedy so a "## Approach" heading inside it cannot end it early.
_BODY_RE = re.compile(
    r"\A\s*## Question\n(.*?)\n## Answer\n(.*)\n## Approach\n(.*?)\s*\Z", re.DOTALL
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by can could do does for from how i if in is it me my "
    "of on or should so that the there this to was what when where which who why "
    "will with would you your".split()
)
_SIMILARITY_THRESHOLD = 0.6
_MAX_CANDIDATES = 3
_MAX_LISTED = 20


def _notes_dir() -> Path:
    configured = os.getenv("ATHOS_NOTES_DIR")
    return Path(configured) if configured else _REPO_ROOT / ".notes"


@dataclass
class _Note:
    name: str
    description: str
    question: str = ""
    answer: str = ""
    approach: str = ""
    created: str = ""


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:_NAME_MAX].rstrip("-")


def _one_line(text: str) -> str:
    return " ".join(text.split())[:_DESCRIPTION_MAX]


def _parse(name: str, text: str) -> Optional[_Note]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    fields = dict(
        line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line
    )
    note = _Note(name, fields.get("description", ""), created=fields.get("created", ""))
    body = _BODY_RE.match(match.group(2))
    if body:
        note.question, note.answer, note.approach = (p.strip() for p in body.groups())
    return note


def _load(root: Path) -> List[_Note]:
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
    return (
        "---\n"
        f"name: {note.name}\n"
        f"description: {_one_line(note.description)}\n"
        f"created: {note.created or now}\n"
        f"updated: {now}\n"
        "---\n\n"
        f"## Question\n{note.question.strip()}\n\n"
        f"## Answer\n{note.answer.strip()}\n\n"
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


def _find_similar(question: str, notes: List[_Note]) -> List[_Note]:
    scored = [(_similarity(question, note.question), note) for note in notes]
    scored = [item for item in scored if item[0] >= _SIMILARITY_THRESHOLD]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [note for _, note in scored[:_MAX_CANDIDATES]]


@contextmanager
def _locked(root: Path) -> Iterator[None]:
    with open(root / ".notes.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _save(root: Path, note: _Note) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _write_atomic(root / note.name / _NOTE_FILE, _render(note, now))


def _candidates_message(candidates: List[_Note]) -> str:
    lines = [
        "Similar note(s) already exist, so nothing was saved yet. Compare them with "
        "the current question and your answer, then call note_taker again with the "
        "same arguments plus one decision:",
        "- decision='update', note_name=N: note N asks the same thing, but your "
        "answer is more correct or complete. Your answer and note replace it, so "
        "fold in anything from note N that is still correct.",
        "- decision='no_change', note_name=N: note N asks the same thing and its "
        "answer is already correct and complete.",
        "- decision='new': none of these asks the same thing.",
    ]
    for note in candidates:
        lines += [
            "",
            f"[note_name={note.name}]",
            f"Description: {note.description}",
            f"Question: {note.question}",
            f"Answer: {note.answer}",
            f"Approach: {note.approach}",
        ]
    return "\n".join(lines)


@tool
def note_taker(
    name: str,
    description: str,
    question: str,
    answer: str,
    note: str,
    decision: Optional[Literal["new", "update", "no_change"]] = None,
    note_name: Optional[str] = None,
) -> str:
    """Save the user's question, your final answer and your approach as a reusable note.

    Each note is stored like a skill: a folder named `name` holding a
    note.md. Call this when your final answer is ready but before you send
    it. Leave `decision` unset on the first call. If similar notes already
    exist, nothing is saved and they are shown to you; compare, then call
    again with a decision. After this tool confirms, reply to the user with
    your final answer.

    Args:
        name: Short folder name for the note: lowercase words joined by
            hyphens, e.g. "perlmutter-gpus-per-node" (max 64 characters).
        description: One sentence saying what the note covers and when to use
            it, e.g. "How many GPUs a Perlmutter GPU node has; use for node
            hardware questions." This is what list_notes shows later.
        question: The user's question, as asked.
        answer: The final answer you are about to give the user, in full.
        note: A short reflection on how you solved it, in the form "For this
            problem, I took this approach, because ...". Mention which
            tools/collections you used, what worked or didn't, and why the
            answer is justified.
        decision: Only on a follow-up call after similar notes were shown:
            'update' to replace note `note_name` with this entry, 'no_change'
            if note `note_name` is already correct, or 'new' to save a
            separate note.
        note_name: The existing note to update or keep, required with
            'update' and 'no_change'. An update keeps that note's name.

    Returns:
        What was saved, or the similar notes to compare against.
    """
    root = _notes_dir()
    root.mkdir(parents=True, exist_ok=True)
    with _locked(root):
        notes = _load(root)
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
            old = names[note_name]
            _save(
                root,
                _Note(note_name, description, question, answer, note, old.created),
            )
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
        _save(root, _Note(slug, description, question, answer, note))
        return f"Saved as note '{slug}'. Now send your final answer to the user."


@tool
def list_notes(query: str = "") -> str:
    """List saved notes (name and description) from earlier solved questions.

    Call this before answering, with the user's question as `query`, to find
    notes on the same or a related problem. Then call read_note with a
    matching name to load its full answer and approach.

    Args:
        query: Words to match against note names, descriptions and questions.
            Leave empty to list notes by name.

    Returns:
        Matching notes as "- name: description" lines, best match first.
    """
    notes = _load(_notes_dir())
    if not notes:
        return "No notes saved yet."
    if query.strip():
        scored = [
            (_similarity(query, f"{n.name} {n.description} {n.question}"), n)
            for n in notes
        ]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        notes = [n for _, n in scored]
        if not notes:
            return f"No notes match '{query}'."
    shown = notes[:_MAX_LISTED]
    lines = [f"- {n.name}: {n.description}" for n in shown]
    if len(notes) > len(shown):
        lines.append(
            f"({len(notes) - len(shown)} more; use a more specific query to narrow.)"
        )
    lines.append("Call read_note with a name to load that note.")
    return "\n".join(lines)


@tool
def read_note(name: str) -> str:
    """Load one saved note's note.md: its question, answer and approach.

    Use a note as a prior solution. If it asks the same thing and its answer
    fully resolves the user's question, answer from it; otherwise fall back to
    the other retrieval tools.

    Args:
        name: The note's name, as shown by list_notes.

    Returns:
        The note's full note.md text.
    """
    path = _notes_dir() / name / _NOTE_FILE
    if not _NAME_RE.match(name) or not path.is_file():
        return f"No note named '{name}'. Call list_notes to see available notes."
    return path.read_text(encoding="utf-8")


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

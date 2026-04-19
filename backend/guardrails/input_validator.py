"""
Deterministic input validation — runs before any AI agent is invoked.
Fast, cheap, and certain. If any rule fails the pipeline is never called.
"""
import re
from fastapi import HTTPException

MIN_NOTE_LENGTH = 50
MAX_NOTE_LENGTH = 10_000
PATIENT_ID_PATTERN = re.compile(r'^[A-Za-z0-9\-]{3,50}$')

# Prompt injection and abuse patterns
_INJECTION_MARKERS = [
    "select * from", "drop table", "delete from",
    "<script", "javascript:", "onerror=",
    "ignore previous instructions", "ignore all previous",
    "you are now", "act as a different", "pretend you are",
    "disregard your instructions", "new instruction:",
    "system prompt:", "### instruction",
]

# Trivial/test submissions that carry no clinical value
_TRIVIAL_PATTERNS = [
    re.compile(r'^(.)\1{10,}$'),          # 10+ repeated chars: "aaaaaaaaa"
    re.compile(r'^(test|hello|hi|foo|bar|asdf|qwerty)[\s\W]*$', re.I),
    re.compile(r'^[^a-zA-Z]{0,5}$'),      # essentially empty or punctuation only
]


def validate_case_input(patient_id: str, raw_note: str) -> None:
    """
    Validates patient_id and raw_note before the graph runs.
    Raises HTTPException(400) on any failure.
    """
    # --- Patient ID ---
    if not patient_id or not patient_id.strip():
        raise HTTPException(status_code=400, detail="Patient ID is required.")

    if not PATIENT_ID_PATTERN.match(patient_id.strip()):
        raise HTTPException(
            status_code=400,
            detail=(
                "Patient ID must be 3–50 alphanumeric characters. "
                "Dashes are allowed. Example: PT-00123"
            ),
        )

    # --- Note length ---
    note = raw_note.strip()
    if len(note) < MIN_NOTE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Clinical note is too short ({len(note)} characters). "
                f"A minimum of {MIN_NOTE_LENGTH} characters is required for meaningful analysis."
            ),
        )

    if len(note) > MAX_NOTE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Clinical note exceeds the maximum allowed length "
                f"({len(note):,} / {MAX_NOTE_LENGTH:,} characters)."
            ),
        )

    # --- Trivial / non-clinical content ---
    for pattern in _TRIVIAL_PATTERNS:
        if pattern.match(note):
            raise HTTPException(
                status_code=400,
                detail="Clinical note does not appear to contain valid medical content.",
            )

    # --- Prompt injection ---
    note_lower = note.lower()
    for marker in _INJECTION_MARKERS:
        if marker in note_lower:
            raise HTTPException(
                status_code=400,
                detail="Invalid content detected in clinical note.",
            )

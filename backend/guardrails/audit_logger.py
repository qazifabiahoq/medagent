"""
Structured audit logger for HIPAA-adjacent compliance.

Key design decisions:
- Patient IDs are one-way hashed (SHA-256) before logging. Raw PII never appears in logs.
- Raw clinical note content is never logged — only metadata (length, flag counts).
- Every case submission, agent completion, and clinician decision is recorded.
- Logs are structured JSON for easy ingestion by log aggregators (Datadog, CloudWatch, etc.).

HIPAA (Health Insurance Portability and Accountability Act): US federal law that sets
standards for protecting sensitive patient health information. Even though MedAgent is
a research/demo system, these practices mirror what a HIPAA-compliant deployment requires.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

_logger = logging.getLogger("medagent.audit")

if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_pii(value: str) -> str:
    """
    One-way SHA-256 hash of patient-identifiable data.
    Produces a 12-character hex prefix — enough to correlate logs
    without exposing the raw patient ID.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _emit(entry: dict) -> None:
    _logger.info(json.dumps(entry))


def log_case_submitted(
    patient_id: str,
    thread_id: str,
    note_length: int,
    emergency_flags: list,
) -> None:
    """Logged when a new case is accepted and the graph is about to start."""
    _emit({
        "event": "case_submitted",
        "timestamp": _now(),
        "thread_id": thread_id,
        "patient_id_hash": _hash_pii(patient_id),
        "note_length_chars": note_length,
        "guardrail_emergency_flags": len(emergency_flags),
        "emergency_severities": [f.get("severity") for f in emergency_flags],
    })


def log_case_rejected(patient_id: str, reason: str) -> None:
    """Logged when input validation rejects a case before the graph runs."""
    _emit({
        "event": "case_rejected",
        "timestamp": _now(),
        "patient_id_hash": _hash_pii(patient_id) if patient_id else "unknown",
        "rejection_reason": reason,
    })


def log_agent_complete(
    thread_id: str,
    agent_name: str,
    duration_ms: int,
    success: bool,
    error: str | None = None,
) -> None:
    """Logged when any agent node finishes execution."""
    _emit({
        "event": "agent_complete",
        "timestamp": _now(),
        "thread_id": thread_id,
        "agent": agent_name,
        "duration_ms": duration_ms,
        "success": success,
        **({"error": error} if error else {}),
    })


def log_clinician_decision(
    thread_id: str,
    patient_id: str,
    approved: bool,
) -> None:
    """
    Logged when a clinician makes an approval decision at the HITL gate.
    This record is critical for audit trails in regulated environments.
    """
    _emit({
        "event": "clinician_decision",
        "timestamp": _now(),
        "thread_id": thread_id,
        "patient_id_hash": _hash_pii(patient_id),
        "decision": "approved" if approved else "rejected",
    })


def log_rate_limit_hit(ip_hash: str) -> None:
    """Logged when a client exceeds the submission rate limit."""
    _emit({
        "event": "rate_limit_exceeded",
        "timestamp": _now(),
        "ip_hash": ip_hash,
    })

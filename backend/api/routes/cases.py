from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import uuid
import asyncio

from graph.builder import build_graph
from graph.state import AgentState
from memory.short_term import ShortTermMemory
from guardrails.input_validator import validate_case_input
from guardrails.emergency_detector import detect_emergencies
from guardrails.rate_limiter import check_rate_limit
from guardrails.audit_logger import log_case_submitted, log_case_rejected

router = APIRouter()

# In-memory store: thread_id -> initial AgentState
# The stream endpoint picks this up and runs the graph while streaming events
_pending: dict[str, AgentState] = {}


class CaseRequest(BaseModel):
    patient_id: str
    raw_note: str


@router.post("/")
async def submit_case(body: CaseRequest, request: Request):
    # 1. Rate limiting
    check_rate_limit(request)

    # 2. Input validation
    try:
        validate_case_input(body.patient_id, body.raw_note)
    except HTTPException as exc:
        log_case_rejected(body.patient_id, exc.detail)
        raise

    # 3. Emergency detection (deterministic, microseconds)
    emergency_flags = detect_emergencies(body.raw_note)

    # 4. Audit log
    thread_id = str(uuid.uuid4())
    log_case_submitted(
        patient_id=body.patient_id,
        thread_id=thread_id,
        note_length=len(body.raw_note),
        emergency_flags=emergency_flags,
    )

    # 5. Store initial state — the stream endpoint runs the graph so events
    #    are visible in the UI as each agent completes
    _pending[thread_id] = {
        "thread_id": thread_id,
        "patient_id": body.patient_id,
        "raw_note": body.raw_note,
        "emergency_flags": emergency_flags,
        "guardrail_warnings": [],
        "intake_payload": None,
        "prior_sessions": None,
        "evidence_chunks": None,
        "differential": None,
        "reflection_count": 0,
        "risk_flags": None,
        "department_routing": None,
        "soap_note": None,
        "next_agent": None,
        "completed_agents": [],
        "error": None,
        "awaiting_approval": False,
        "approved": False,
        "messages": [],
    }

    return {
        "thread_id": thread_id,
        "status": "pending",
        "emergency_flags": emergency_flags,
    }


def pop_pending(thread_id: str) -> AgentState | None:
    return _pending.pop(thread_id, None)


@router.get("/{thread_id}/state")
async def get_case_state(thread_id: str):
    stm = ShortTermMemory()
    try:
        working = await stm.get_working_memory(thread_id)
    finally:
        await stm.close()

    if not working:
        raise HTTPException(status_code=404, detail="No working state found for this thread")

    return {"thread_id": thread_id, "state": working}

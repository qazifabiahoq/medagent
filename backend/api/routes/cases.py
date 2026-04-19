from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import uuid

from graph.builder import build_graph
from graph.state import AgentState
from memory.short_term import ShortTermMemory
from guardrails.input_validator import validate_case_input
from guardrails.emergency_detector import detect_emergencies
from guardrails.rate_limiter import check_rate_limit
from guardrails.audit_logger import log_case_submitted, log_case_rejected

router = APIRouter()


class CaseRequest(BaseModel):
    patient_id: str
    raw_note: str


@router.post("/")
async def submit_case(body: CaseRequest, request: Request):
    # 1. Rate limiting — checked before anything else
    check_rate_limit(request)

    # 2. Deterministic input validation — no AI called if this fails
    try:
        validate_case_input(body.patient_id, body.raw_note)
    except HTTPException as exc:
        log_case_rejected(body.patient_id, exc.detail)
        raise

    # 3. Emergency detection — deterministic keyword scan, runs in microseconds
    emergency_flags = detect_emergencies(body.raw_note)

    # 4. Audit: record submission (hashed PII, no raw note content)
    thread_id = str(uuid.uuid4())
    log_case_submitted(
        patient_id=body.patient_id,
        thread_id=thread_id,
        note_length=len(body.raw_note),
        emergency_flags=emergency_flags,
    )

    # 5. Build graph and set initial state
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)

    initial_state: AgentState = {
        "thread_id": thread_id,
        "patient_id": body.patient_id,
        "raw_note": body.raw_note,
        # Guardrail outputs pre-populated so agents can read them
        "emergency_flags": emergency_flags,
        "guardrail_warnings": [],
        "intake_payload": None,
        "prior_sessions": None,
        "evidence_chunks": None,
        "differential": None,
        "reflection_count": 0,
        "risk_flags": None,
        "soap_note": None,
        "next_agent": None,
        "completed_agents": [],
        "error": None,
        "awaiting_approval": False,
        "approved": False,
        "messages": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "thread_id": thread_id,
        "status": "running",
        # Return emergency flags immediately so the frontend can show them
        # before the full AI pipeline completes
        "emergency_flags": emergency_flags,
    }


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

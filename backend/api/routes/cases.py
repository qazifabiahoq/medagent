from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import uuid
from graph.builder import build_graph
from graph.state import AgentState

router = APIRouter()


class CaseRequest(BaseModel):
    patient_id: str
    raw_note: str


@router.post("/")
async def submit_case(body: CaseRequest, request: Request):
    thread_id = str(uuid.uuid4())
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)

    initial_state: AgentState = {
        "thread_id": thread_id,
        "patient_id": body.patient_id,
        "raw_note": body.raw_note,
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

    return {"thread_id": thread_id, "status": "running"}

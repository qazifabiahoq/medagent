from fastapi import APIRouter, Request, HTTPException
from graph.builder import build_graph
from guardrails.audit_logger import log_clinician_decision

router = APIRouter()


@router.post("/{thread_id}")
async def approve_case(thread_id: str, request: Request):
    """
    HITL gate. Records the clinician's approval decision and marks the thread
    ready to resume. The frontend reconnects to the SSE stream, which calls
    astream_events(None, ...) to resume the graph from the interrupt point
    and stream the Summarizer agent events back in real time.
    """
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await graph.aget_state(config)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Thread not found")

        state_values = snapshot.values if hasattr(snapshot, "values") else {}
        patient_id = state_values.get("patient_id", "unknown")

        log_clinician_decision(thread_id=thread_id, patient_id=patient_id, approved=True)

        return {"thread_id": thread_id, "status": "approved"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

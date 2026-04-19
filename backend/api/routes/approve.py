from fastapi import APIRouter, Request, HTTPException
from graph.builder import build_graph
from guardrails.audit_logger import log_clinician_decision

router = APIRouter()


@router.post("/{thread_id}")
async def approve_case(thread_id: str, request: Request):
    """
    HITL gate — clinician calls this after reviewing the differential and risk output.
    Resumes the LangGraph from the interrupt checkpoint and runs the Summarizer Agent
    to produce the final SOAP note.

    No SOAP note is ever generated without a human explicitly calling this endpoint.
    """
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await graph.aget_state(config)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Extract patient_id from the checkpoint state for audit logging
        state_values = snapshot.values if hasattr(snapshot, "values") else {}
        patient_id = state_values.get("patient_id", "unknown")

        # Audit: record the clinician's approval decision
        log_clinician_decision(thread_id=thread_id, patient_id=patient_id, approved=True)

        # Resume graph from the LangGraph interrupt
        await graph.ainvoke(None, config=config)

        return {"thread_id": thread_id, "status": "approved"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

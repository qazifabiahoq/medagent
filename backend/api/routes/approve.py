from fastapi import APIRouter, Request, HTTPException
from graph.builder import build_graph

router = APIRouter()


@router.post("/{thread_id}")
async def approve_case(thread_id: str, request: Request):
    """
    HITL gate. Clinician calls this to resume the graph after reviewing
    the differential and risk output. Graph resumes from the interrupt
    checkpoint and runs the summarizer agent to produce the final SOAP note.
    """
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await graph.aget_state(config)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Resume graph from interrupt - passes None as the update to continue
        await graph.ainvoke(None, config=config)
        return {"thread_id": thread_id, "status": "approved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

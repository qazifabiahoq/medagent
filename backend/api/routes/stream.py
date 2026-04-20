from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from graph.builder import build_graph
from api.routes.cases import pop_pending
import json

router = APIRouter()

AGENT_NAMES = {"intake", "history", "research", "differential", "risk", "summarizer"}


@router.get("/{thread_id}")
async def stream_case(thread_id: str, request: Request):
    checkpointer = request.app.state.checkpointer
    initial_state = pop_pending(thread_id)

    async def generate():
        try:
            graph = build_graph(checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            source = initial_state if initial_state is not None else None

            async for event in graph.astream_events(source, config=config, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")

                if kind == "on_chain_start" and name in AGENT_NAMES:
                    yield f"event: agent_start\ndata: {json.dumps({'agent': name})}\n\n"

                elif kind == "on_chain_end" and name in AGENT_NAMES:
                    output = event.get("data", {}).get("output", {})
                    yield f"event: agent_done\ndata: {json.dumps({'agent': name, 'output': output})}\n\n"

                elif kind == "on_chain_end" and name == "__interrupt__":
                    yield f"event: awaiting_approval\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
                    return

            yield f"event: done\ndata: {json.dumps({'thread_id': thread_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

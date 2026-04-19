from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from graph.builder import build_graph
from api.routes.cases import pop_pending
import json
import os

router = APIRouter()

AGENT_NAMES = {"intake", "history", "research", "differential", "risk", "summarizer"}
ALLOWED_ORIGIN = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")[0]


@router.get("/{thread_id}")
async def stream_case(thread_id: str, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = pop_pending(thread_id)

    origin = request.headers.get("origin", ALLOWED_ORIGIN)

    async def generate():
        try:
            source = initial_state if initial_state is not None else None

            async for event in graph.astream_events(source, config=config, version="v2"):
                if await request.is_disconnected():
                    break

                kind = event.get("event")
                name = event.get("name", "")

                if kind == "on_chain_start" and name in AGENT_NAMES:
                    data = json.dumps({"agent": name})
                    yield f"event: agent_start\ndata: {data}\n\n"

                elif kind == "on_chain_end" and name in AGENT_NAMES:
                    output = event.get("data", {}).get("output", {})
                    data = json.dumps({"agent": name, "output": output})
                    yield f"event: agent_done\ndata: {data}\n\n"

                elif kind == "on_chain_end" and name == "__interrupt__":
                    data = json.dumps({"thread_id": thread_id})
                    yield f"event: awaiting_approval\ndata: {data}\n\n"
                    return

            yield f"event: done\ndata: {json.dumps({'thread_id': thread_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from graph.builder import build_graph
import json

router = APIRouter()


@router.get("/{thread_id}")
async def stream_case(thread_id: str, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        async for event in graph.astream_events({}, config=config, version="v2"):
            if await request.is_disconnected():
                break

            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in [
                "intake", "history", "research", "differential", "risk", "summarizer"
            ]:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": name}),
                }

            elif kind == "on_chain_end" and name in [
                "intake", "history", "research", "differential", "risk", "summarizer"
            ]:
                output = event.get("data", {}).get("output", {})
                yield {
                    "event": "agent_done",
                    "data": json.dumps({"agent": name, "output": output}),
                }

            elif kind == "on_chain_end" and name == "__interrupt__":
                yield {
                    "event": "awaiting_approval",
                    "data": json.dumps({"thread_id": thread_id}),
                }

        yield {"event": "done", "data": json.dumps({"thread_id": thread_id})}

    return EventSourceResponse(event_generator())

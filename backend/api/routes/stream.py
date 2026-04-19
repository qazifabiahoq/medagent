from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from graph.builder import build_graph
from api.routes.cases import pop_pending
import json

router = APIRouter()

AGENT_NAMES = {"intake", "history", "research", "differential", "risk", "summarizer"}


@router.get("/{thread_id}")
async def stream_case(thread_id: str, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    # Pick up the initial state stored by POST /cases/ (first connection only)
    initial_state = pop_pending(thread_id)

    async def event_generator():
        if await request.is_disconnected():
            return

        # Fresh run: use initial_state. Post-approval resume: pass None so
        # LangGraph loads the checkpoint and continues from the interrupt.
        source = initial_state if initial_state is not None else None

        async for event in graph.astream_events(source, config=config, version="v2"):
            if await request.is_disconnected():
                break

            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in AGENT_NAMES:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": name}),
                }

            elif kind == "on_chain_end" and name in AGENT_NAMES:
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
                return  # hold — resume after approval

        yield {"event": "done", "data": json.dumps({"thread_id": thread_id})}

    return EventSourceResponse(event_generator())

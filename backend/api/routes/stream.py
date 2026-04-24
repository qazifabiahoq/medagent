from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from graph.builder import build_graph
from api.routes.cases import pop_pending
import json

router = APIRouter()

AGENT_NAMES = {"intake", "history", "research", "differential", "risk", "department_router", "summarizer"}


@router.get("/{thread_id}")
async def stream_case(thread_id: str, request: Request):
    checkpointer = request.app.state.checkpointer
    initial_state = pop_pending(thread_id)

    async def generate():
        try:
            graph = build_graph(checkpointer)
            config = {"configurable": {"thread_id": thread_id}}

            # astream(stream_mode="updates") is the correct LangGraph 1.x API.
            # It yields {node_name: state_update} for every node that runs —
            # no event-name guessing needed.
            async for chunk in graph.astream(
                initial_state, config=config, stream_mode="updates"
            ):
                for node_name, update in chunk.items():
                    if node_name.startswith("__"):
                        continue  # skip internal LangGraph nodes

                    if node_name in AGENT_NAMES:
                        yield f"event: agent_start\ndata: {json.dumps({'agent': node_name})}\n\n"
                        yield (
                            f"event: agent_done\n"
                            f"data: {json.dumps({'agent': node_name, 'output': update}, default=str)}\n\n"
                        )

            # After the stream ends, check if the graph paused at an interrupt
            if checkpointer:
                try:
                    snapshot = await graph.aget_state(config)
                    if snapshot and snapshot.next:
                        yield f"event: awaiting_approval\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
                        return
                except Exception:
                    pass

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

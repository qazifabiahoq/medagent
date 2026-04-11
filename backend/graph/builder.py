from typing import Callable
from langgraph.graph import StateGraph, END

from graph.checkpointer import create_checkpointer
from graph.state import AgentState
from graph.edges import route_after_intake, route_after_differential, route_after_risk
from agents.supervisor import supervisor_node
from agents.intake import intake_node
from agents.history import history_node
from agents.research import research_node
from agents.differential import differential_node
from agents.risk import risk_node
from agents.summarizer import summarizer_node
from memory.short_term import ShortTermMemory


def _with_redis_persistence(node_fn: Callable) -> Callable:
    """
    Wraps an agent node so its output state is mirrored to Redis after every
    execution. This gives all agents shared access to the latest working memory
    and enables session restore if the connection drops before the graph completes.
    """
    async def wrapped(state: AgentState) -> AgentState:
        result = await node_fn(state)
        thread_id = result.get("thread_id") or state.get("thread_id")
        if thread_id:
            stm = ShortTermMemory()
            try:
                await stm.set_working_memory(thread_id, result)
            finally:
                await stm.close()
        return result
    wrapped.__name__ = node_fn.__name__
    return wrapped


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    # Register all agent nodes, each wrapped with Redis working-memory persistence
    graph.add_node("supervisor", _with_redis_persistence(supervisor_node))
    graph.add_node("intake",     _with_redis_persistence(intake_node))
    graph.add_node("history",    _with_redis_persistence(history_node))
    graph.add_node("research",   _with_redis_persistence(research_node))
    graph.add_node("differential", _with_redis_persistence(differential_node))
    graph.add_node("risk",       _with_redis_persistence(risk_node))
    graph.add_node("summarizer", _with_redis_persistence(summarizer_node))

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to intake first
    graph.add_edge("supervisor", "intake")

    # After intake: fan out to history and research in parallel
    graph.add_conditional_edges("intake", route_after_intake, {
        "parallel": ["history", "research"],
        "error": END,
    })

    # Both parallel branches converge at differential.
    # LangGraph's superstep model holds differential until BOTH history and
    # research have written their outputs — no explicit wait loop needed.
    graph.add_edge("history", "differential")
    graph.add_edge("research", "differential")

    # Differential agent with reflection loop
    graph.add_conditional_edges("differential", route_after_differential, {
        "reflect": "differential",
        "risk": "risk",
    })

    # Risk agent routes to summarizer or loops back on critical flags
    graph.add_conditional_edges("risk", route_after_risk, {
        "summarizer": "summarizer",
        "differential": "differential",
    })

    # Summarizer is a HITL interrupt node - graph pauses here for approval
    graph.add_edge("summarizer", END)

    return graph.compile(checkpointer=checkpointer, interrupt_before=["summarizer"])


async def get_checkpointer(postgres_url: str):
    return await create_checkpointer(postgres_url)

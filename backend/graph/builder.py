import logging
from typing import Callable
from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.edges import route_after_intake, route_after_differential
from agents.supervisor import supervisor_node
from agents.intake import intake_node
from agents.history import history_node
from agents.research import research_node
from agents.differential import differential_node
from agents.risk import risk_node
from agents.summarizer import summarizer_node
from agents.department_router import department_router_node
from memory.short_term import ShortTermMemory

logger = logging.getLogger("medagent.graph")


def _with_redis_persistence(node_fn: Callable) -> Callable:
    """
    Mirrors agent output to Redis after each node so working memory is available
    across the pipeline. Redis failure is non-fatal — the graph continues.
    """
    async def wrapped(state: AgentState) -> AgentState:
        result = await node_fn(state)
        thread_id = result.get("thread_id") or state.get("thread_id")
        if thread_id:
            stm = ShortTermMemory()
            try:
                await stm.set_working_memory(thread_id, result)
            except Exception as e:
                logger.warning("Redis persistence skipped for %s: %s", node_fn.__name__, e)
            finally:
                try:
                    await stm.close()
                except Exception:
                    pass
        return result
    wrapped.__name__ = node_fn.__name__
    return wrapped


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("supervisor",   _with_redis_persistence(supervisor_node))
    graph.add_node("intake",       _with_redis_persistence(intake_node))
    graph.add_node("history",      _with_redis_persistence(history_node))
    graph.add_node("research",     _with_redis_persistence(research_node))
    graph.add_node("differential", _with_redis_persistence(differential_node))
    graph.add_node("risk",              _with_redis_persistence(risk_node))
    graph.add_node("department_router", department_router_node)
    graph.add_node("summarizer",        _with_redis_persistence(summarizer_node))

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "intake")

    # Sequential: intake → history → research → differential
    # (LangGraph 1.x requires string returns from conditional edges, not lists)
    graph.add_conditional_edges("intake", route_after_intake, {
        "history": "history",
        "end": END,
    })

    graph.add_edge("history", "research")
    graph.add_edge("research", "differential")

    graph.add_conditional_edges("differential", route_after_differential, {
        "reflect": "differential",
        "risk": "risk",
    })

    graph.add_edge("risk", "department_router")

    graph.add_edge("department_router", "summarizer")
    graph.add_edge("summarizer", END)

    # interrupt_before requires a checkpointer to save/restore state.
    # Without one, run straight through so the SOAP note is always generated.
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["summarizer"] if checkpointer else [],
    )

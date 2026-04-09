from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from graph.state import AgentState
from graph.edges import route_after_intake, route_after_parallel, route_after_differential, route_after_risk
from agents.supervisor import supervisor_node
from agents.intake import intake_node
from agents.history import history_node
from agents.research import research_node
from agents.differential import differential_node
from agents.risk import risk_node
from agents.summarizer import summarizer_node


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    # Register all agent nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("intake", intake_node)
    graph.add_node("history", history_node)
    graph.add_node("research", research_node)
    graph.add_node("differential", differential_node)
    graph.add_node("risk", risk_node)
    graph.add_node("summarizer", summarizer_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to intake first
    graph.add_edge("supervisor", "intake")

    # After intake: fan out to history and research in parallel
    graph.add_conditional_edges("intake", route_after_intake, {
        "parallel": ["history", "research"],
        "error": END,
    })

    # After both parallel agents complete: route to differential
    graph.add_conditional_edges("history", route_after_parallel, {
        "wait": "history",
        "differential": "differential",
    })
    graph.add_conditional_edges("research", route_after_parallel, {
        "wait": "research",
        "differential": "differential",
    })

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
    checkpointer = AsyncPostgresSaver.from_conn_string(postgres_url)
    await checkpointer.setup()
    return checkpointer

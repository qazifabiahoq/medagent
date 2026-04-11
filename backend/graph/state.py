from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


def _merge_lists(a: list, b: list) -> list:
    """Reducer for completed_agents: union of both lists, preserving order."""
    seen = set(a)
    return a + [x for x in b if x not in seen]


class AgentState(TypedDict):
    # Core identifiers
    thread_id: str
    patient_id: str

    # Input
    raw_note: str

    # Intake agent output
    intake_payload: Optional[dict]

    # History agent output
    prior_sessions: Optional[list]

    # Research agent output
    evidence_chunks: Optional[list]

    # Differential agent output
    differential: Optional[list]
    reflection_count: int

    # Risk agent output
    risk_flags: Optional[list]

    # Final output
    soap_note: Optional[dict]

    # Orchestration
    next_agent: Optional[str]
    # Reducer ensures parallel branches (history + research) both get recorded
    completed_agents: Annotated[list, _merge_lists]
    error: Optional[str]

    # HITL
    awaiting_approval: bool
    approved: bool

    # Conversation messages (for agents that use chat history)
    messages: Annotated[list, add_messages]

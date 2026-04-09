from graph.state import AgentState


async def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor agent. Entry point for every case.
    Validates input, initializes orchestration state, and hands off to intake.
    Does not call the LLM directly. Pure orchestration logic.
    """
    if not state.get("raw_note"):
        return {**state, "error": "No clinical note provided"}

    if not state.get("patient_id"):
        return {**state, "error": "No patient ID provided"}

    return {
        **state,
        "completed_agents": [],
        "reflection_count": 0,
        "awaiting_approval": False,
        "approved": False,
        "error": None,
    }

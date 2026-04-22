from graph.state import AgentState

MAX_REFLECTIONS = 3


def route_after_intake(state: AgentState) -> str:
    if state.get("error") or not state.get("intake_payload"):
        return "end"
    return "history"


def route_after_differential(state: AgentState) -> str:
    reflection_count = state.get("reflection_count", 0)
    differential = state.get("differential", [])

    # Reflect if under max and quality is low (differential agent sets a quality flag)
    needs_reflection = any(d.get("needs_revision") for d in differential)

    if needs_reflection and reflection_count < MAX_REFLECTIONS:
        return "reflect"
    return "risk"


def route_after_risk(state: AgentState) -> str:
    risk_flags = state.get("risk_flags", [])
    critical = [f for f in risk_flags if f.get("severity") == "critical"]
    if critical:
        return "differential"
    return "department_router"

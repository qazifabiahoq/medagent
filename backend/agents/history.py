import logging
from graph.state import AgentState
from memory.long_term import LongTermMemory
from memory.embedder import get_embedder

logger = logging.getLogger("medagent.history")


async def history_node(state: AgentState) -> AgentState:
    patient_id = state["patient_id"]
    intake_payload = state.get("intake_payload", {})
    history_flags = intake_payload.get("history_flags", [])
    query_text = " ".join(history_flags) if history_flags else patient_id

    completed = state.get("completed_agents", [])

    try:
        query_embedding = await get_embedder().aembed_query(query_text)

        memory = LongTermMemory()
        try:
            prior_sessions = memory.retrieve_patient_history(
                patient_id=patient_id,
                query_embedding=query_embedding,
                limit=5,
            )
        finally:
            memory.close()

    except Exception as e:
        logger.warning("History retrieval unavailable, continuing without: %s", e)
        prior_sessions = []

    return {
        **state,
        "prior_sessions": prior_sessions,
        "completed_agents": completed + ["history"],
    }

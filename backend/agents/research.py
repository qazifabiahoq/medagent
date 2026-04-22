import logging
from graph.state import AgentState
from memory.long_term import LongTermMemory
from memory.embedder import get_embedder

logger = logging.getLogger("medagent.research")


async def research_node(state: AgentState) -> AgentState:
    intake_payload = state.get("intake_payload", {})
    symptoms = intake_payload.get("symptoms", [])
    assessment_hints = intake_payload.get("assessment_hints", [])
    query_text = " ".join(symptoms + assessment_hints)

    completed = state.get("completed_agents", [])

    if not query_text.strip():
        return {**state, "evidence_chunks": [], "completed_agents": completed + ["research"]}

    try:
        query_embedding = await get_embedder().aembed_query(query_text)

        memory = LongTermMemory()
        try:
            evidence_chunks = memory.retrieve_evidence(
                query=query_text,
                query_embedding=query_embedding,
                limit=8,
            )
        finally:
            memory.close()

    except Exception as e:
        logger.warning("Research retrieval unavailable, continuing without: %s", e)
        evidence_chunks = []

    return {
        **state,
        "evidence_chunks": evidence_chunks,
        "completed_agents": completed + ["research"],
    }

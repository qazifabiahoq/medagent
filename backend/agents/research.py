import logging
from langchain_huggingface import HuggingFaceEmbeddings
import os
from graph.state import AgentState
from memory.long_term import LongTermMemory

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
        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
        )
        query_embedding = await embedder.aembed_query(query_text)

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

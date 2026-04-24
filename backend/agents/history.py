import logging
from graph.state import AgentState

logger = logging.getLogger("medagent.history")


async def history_node(state: AgentState) -> AgentState:
    """
    History agent. Queries Qdrant for prior patient sessions.
    Returns empty list when Qdrant/embeddings unavailable — pipeline continues.
    """
    completed = state.get("completed_agents", [])
    prior_sessions = []

    try:
        from memory.long_term import LongTermMemory
        import os

        patient_id = state["patient_id"]
        intake_payload = state.get("intake_payload") or {}
        history_flags = intake_payload.get("history_flags", [])
        query_text = " ".join(history_flags) if history_flags else patient_id

        if not os.getenv("QDRANT_URL") or not os.getenv("HUGGINGFACE_API_TOKEN"):
            raise ValueError("Qdrant/HuggingFace not configured")

        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        embedder = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_TOKEN"),
        )
        query_embedding = await embedder.aembed_query(query_text)

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
        logger.info("History retrieval skipped: %s", e)

    return {
        **state,
        "prior_sessions": prior_sessions,
        "completed_agents": completed + ["history"],
    }

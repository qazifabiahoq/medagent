import logging
from graph.state import AgentState

logger = logging.getLogger("medagent.research")


async def research_node(state: AgentState) -> AgentState:
    """
    Research agent. Semantic retrieval over medical knowledge base in Qdrant.
    Returns empty list when Qdrant/embeddings unavailable — pipeline continues.
    """
    completed = state.get("completed_agents", [])
    evidence_chunks = []

    try:
        import os

        if not os.getenv("QDRANT_URL") or not os.getenv("HUGGINGFACE_API_TOKEN"):
            raise ValueError("Qdrant/HuggingFace not configured")

        intake_payload = state.get("intake_payload") or {}
        symptoms = intake_payload.get("symptoms", [])
        assessment_hints = intake_payload.get("assessment_hints", [])
        query_text = " ".join(symptoms + assessment_hints)

        if not query_text.strip():
            raise ValueError("No query text")

        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        from memory.long_term import LongTermMemory

        embedder = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_TOKEN"),
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
        logger.info("Research retrieval skipped: %s", e)

    return {
        **state,
        "evidence_chunks": evidence_chunks,
        "completed_agents": completed + ["research"],
    }

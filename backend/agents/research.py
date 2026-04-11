from langchain_huggingface import HuggingFaceEndpointEmbeddings
import os
from graph.state import AgentState
from memory.long_term import LongTermMemory


async def research_node(state: AgentState) -> AgentState:
    """
    Research agent. Semantic retrieval over medical knowledge base in Qdrant.
    Retrieves clinical guideline chunks and evidence relevant to the case.
    Runs in parallel with history agent after intake completes.
    """
    intake_payload = state.get("intake_payload", {})

    symptoms = intake_payload.get("symptoms", [])
    assessment_hints = intake_payload.get("assessment_hints", [])
    query_text = " ".join(symptoms + assessment_hints)

    if not query_text.strip():
        completed = state.get("completed_agents", [])
        return {
            **state,
            "evidence_chunks": [],
            "completed_agents": completed + ["research"],
        }

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

    completed = state.get("completed_agents", [])
    return {
        **state,
        "evidence_chunks": evidence_chunks,
        "completed_agents": completed + ["research"],
    }

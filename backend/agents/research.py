from langchain_ollama import OllamaEmbeddings
import os
from graph.state import AgentState
from memory.long_term import LongTermMemory


async def research_node(state: AgentState) -> AgentState:
    """
    Research agent. Hybrid RAG retrieval over medical knowledge base in Weaviate.
    Retrieves clinical guideline chunks and PubMed evidence relevant to the case.
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

    embedder = OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
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

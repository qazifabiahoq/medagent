from langchain_huggingface import HuggingFaceEndpointEmbeddings
import os
from graph.state import AgentState
from memory.long_term import LongTermMemory


async def history_node(state: AgentState) -> AgentState:
    """
    History agent. Queries Qdrant long-term memory for prior patient sessions.
    Uses patient_id scoping and semantic similarity on intake payload summary.
    Runs in parallel with research agent after intake completes.
    """
    patient_id = state["patient_id"]
    intake_payload = state.get("intake_payload", {})

    history_flags = intake_payload.get("history_flags", [])
    query_text = " ".join(history_flags) if history_flags else patient_id

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

    completed = state.get("completed_agents", [])
    return {
        **state,
        "prior_sessions": prior_sessions,
        "completed_agents": completed + ["history"],
    }

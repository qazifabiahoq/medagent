from fastapi import APIRouter, HTTPException
from langchain_ollama import OllamaEmbeddings
import os
from memory.long_term import LongTermMemory

router = APIRouter()


@router.get("/{patient_id}")
async def get_patient_history(patient_id: str, query: str = ""):
    embedder = OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
    )
    query_text = query if query else patient_id
    query_embedding = await embedder.aembed_query(query_text)

    memory = LongTermMemory()
    try:
        sessions = memory.retrieve_patient_history(
            patient_id=patient_id,
            query_embedding=query_embedding,
            limit=10,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        memory.close()

    return {"patient_id": patient_id, "sessions": sessions}

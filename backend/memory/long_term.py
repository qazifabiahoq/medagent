from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
import uuid
import os

from memory.schemas import (
    PATIENT_SESSION_COLLECTION,
    EVIDENCE_CHUNK_COLLECTION,
    VECTOR_SIZE,
)


class LongTermMemory:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self._ensure_collections()

    def _ensure_collections(self):
        try:
            existing = {c.name for c in self.client.get_collections().collections}
        except Exception:
            existing = set()

        if PATIENT_SESSION_COLLECTION not in existing:
            try:
                self.client.create_collection(
                    collection_name=PATIENT_SESSION_COLLECTION,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )
            except Exception:
                pass

        if EVIDENCE_CHUNK_COLLECTION not in existing:
            try:
                self.client.create_collection(
                    collection_name=EVIDENCE_CHUNK_COLLECTION,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )
            except Exception:
                pass

    def store_session(
        self,
        patient_id: str,
        thread_id: str,
        soap_note: dict,
        summary: str,
        embedding: list,
    ):
        self.client.upsert(
            collection_name=PATIENT_SESSION_COLLECTION,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "patient_id": patient_id,
                        "thread_id": thread_id,
                        "soap_note": str(soap_note),
                        "summary": summary,
                    },
                )
            ],
        )

    def retrieve_patient_history(
        self, patient_id: str, query_embedding: list, limit: int = 5
    ) -> list:
        results = self.client.search(
            collection_name=PATIENT_SESSION_COLLECTION,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[FieldCondition(key="patient_id", match=MatchValue(value=patient_id))]
            ),
            limit=limit,
        )
        return [r.payload for r in results]

    def retrieve_evidence(
        self, query: str, query_embedding: list, limit: int = 8
    ) -> list:
        results = self.client.search(
            collection_name=EVIDENCE_CHUNK_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
        )
        return [r.payload for r in results]

    def close(self):
        # Qdrant client manages its own connection pool
        pass

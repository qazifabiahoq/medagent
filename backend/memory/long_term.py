import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import HybridFusion
import os


class LongTermMemory:
    def __init__(self):
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_URL", "http://weaviate:8080").replace("http://", "").split(":")[0],
            port=int(os.getenv("WEAVIATE_URL", "http://weaviate:8080").split(":")[-1]),
        )
        self._ensure_collections()

    def _ensure_collections(self):
        # PatientSession collection
        if not self.client.collections.exists("PatientSession"):
            self.client.collections.create(
                name="PatientSession",
                properties=[
                    Property(name="patient_id", data_type=DataType.TEXT),
                    Property(name="thread_id", data_type=DataType.TEXT),
                    Property(name="soap_note", data_type=DataType.TEXT),
                    Property(name="summary", data_type=DataType.TEXT),
                    Property(name="created_at", data_type=DataType.DATE),
                ],
                vectorizer_config=Configure.Vectorizer.none(),
            )

        # EvidenceChunk collection for RAG
        if not self.client.collections.exists("EvidenceChunk"):
            self.client.collections.create(
                name="EvidenceChunk",
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="source_type", data_type=DataType.TEXT),
                    Property(name="keywords", data_type=DataType.TEXT_ARRAY),
                ],
                vectorizer_config=Configure.Vectorizer.none(),
            )

    def store_session(self, patient_id: str, thread_id: str, soap_note: dict, summary: str, embedding: list):
        collection = self.client.collections.get("PatientSession")
        collection.data.insert(
            properties={
                "patient_id": patient_id,
                "thread_id": thread_id,
                "soap_note": str(soap_note),
                "summary": summary,
            },
            vector=embedding,
        )

    def retrieve_patient_history(self, patient_id: str, query_embedding: list, limit: int = 5) -> list:
        collection = self.client.collections.get("PatientSession")
        results = collection.query.hybrid(
            query=patient_id,
            vector=query_embedding,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            filters=weaviate.classes.query.Filter.by_property("patient_id").equal(patient_id),
            limit=limit,
            return_properties=["patient_id", "thread_id", "soap_note", "summary"],
        )
        return [obj.properties for obj in results.objects]

    def retrieve_evidence(self, query: str, query_embedding: list, limit: int = 8) -> list:
        collection = self.client.collections.get("EvidenceChunk")
        results = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            limit=limit,
            return_properties=["content", "source", "source_type", "keywords"],
        )
        return [obj.properties for obj in results.objects]

    def close(self):
        self.client.close()

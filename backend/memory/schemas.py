"""
Qdrant collection schema definitions.
LongTermMemory imports these constants so schema is defined in one place.
"""

PATIENT_SESSION_COLLECTION = "PatientSession"
EVIDENCE_CHUNK_COLLECTION = "EvidenceChunk"

# Must match the embedding model output dimension.
# sentence-transformers/all-MiniLM-L6-v2 → 384
VECTOR_SIZE = 384

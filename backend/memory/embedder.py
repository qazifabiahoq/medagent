import logging
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger("medagent.embedder")

_embedder: HuggingFaceEmbeddings | None = None


def get_embedder() -> HuggingFaceEmbeddings:
    global _embedder
    if _embedder is None:
        logger.info("Loading local embedding model...")
        _embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model ready")
    return _embedder

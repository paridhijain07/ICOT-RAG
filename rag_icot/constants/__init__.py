from rag_icot.constants.evidence_facets import (
    EVIDENCE_FACETS,
    FACET_FILTERS,
    VALID_SOURCES,
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "artifacts/chroma_db"
COLLECTION_NAME = "iot_security_kb"

__all__ = [
    "EVIDENCE_FACETS",
    "FACET_FILTERS",
    "VALID_SOURCES",
    "EMBEDDING_MODEL",
    "CHROMA_PERSIST_DIR",
    "COLLECTION_NAME",
]

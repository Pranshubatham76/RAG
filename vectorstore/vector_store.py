# backend/app/vectorstore/vector_store.py
"""
Vector store factory and facade.

Usage:
    from backend.app.vectorstore.vector_store import get_vector_store
    VS = get_vector_store()
    VS.add_documents(docs)
    hits = VS.search(query_vector, top_k=5)
"""

from __future__ import annotations
import os
import logging
from typing import List, Dict, Any, Sequence, Optional

logger = logging.getLogger(__name__)

_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma").lower()

def get_vector_store(store_type: Optional[str] = None, **kwargs) -> Any:
    """
    Factory that returns a store instance based on configuration or explicit store_type arg.
    Additional kwargs forwarded to the backend constructors.
    """
    st = (store_type or _STORE_TYPE).lower()
    if st == "chroma":
        try:
            from .chroma_store import ChromaStore
            return ChromaStore(**kwargs)
        except Exception as e:
            logger.exception("Failed to initialize ChromaStore: %s", e)
            # fallback to faiss if available
            logger.info("Falling back to FAISS store")
            try:
                from .faiss_store import FaissStore
                return FaissStore(**kwargs)
            except Exception as e2:
                logger.exception("Failed to initialize FaissStore fallback: %s", e2)
                raise RuntimeError("No vector store available (chroma failed, faiss failed)") from e2
    elif st == "faiss":
        try:
            from .faiss_store import FaissStore
            return FaissStore(**kwargs)
        except Exception as e:
            logger.exception("Failed to initialize FaissStore: %s", e)
            raise
    else:
        raise ValueError(f"Unknown VECTOR_STORE_TYPE: {st}")

# Simple module-level singleton helper (optional)
_store_instance = None

def get_default_store() -> Any:
    """
    Return a singleton store instance for the app lifetime.
    Calling code can use this, or call get_vector_store() directly.
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = get_vector_store()
    return _store_instance


def insert_chunks(store: Any, chunk_schemas: List[Any]) -> Dict[str, Any]:
    """
    Insert ChunkSchema objects into vector store.
    
    This is a convenience wrapper that converts ChunkSchema objects
    to the format expected by add_documents.
    
    Args:
        store: Vector store instance (ChromaStore or FaissStore)
        chunk_schemas: List of ChunkSchema objects
        
    Returns:
        Dict with status and inserted count
    """
    if not chunk_schemas:
        return {"status": "ok", "inserted": 0}
    
    # Convert ChunkSchema to dict format expected by store
    docs = []
    for chunk_schema in chunk_schemas:
        # Handle both ChunkSchema objects and dicts
        if hasattr(chunk_schema, 'dict'):
            # Pydantic model
            doc = chunk_schema.dict()
        elif hasattr(chunk_schema, '__dict__'):
            # Object with __dict__
            doc = chunk_schema.__dict__
        else:
            # Already a dict
            doc = chunk_schema
        
        docs.append({
            "chunk_id": doc.get("chunk_id"),
            "text": doc.get("text", ""),
            "embedding": doc.get("embedding", []),
            "meta": doc.get("meta", {})
        })
    
    # Use add_documents method
    return store.add_documents(docs)
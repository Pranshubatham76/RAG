"""
Embedder - Convert text chunks into embedding vectors.

Purpose: Convert every chunk into embedding vector of size 768/1024/1536
Input: "This is paragraph one..."
Output: ChunkSchema object with embedding
Returns to: vector_store.py
"""
from typing import List, Dict, Any
import os
import time
import logging
from pathlib import Path

from .model import EmbeddingClient

try:
    from schema.retrieval_schema import ChunkSchema
except ImportError:
    # Fallback for different project structures
    try:
        from ..schema.retrieval_schema import ChunkSchema
    except ImportError:
        # If schema is not available, use dict-based approach
        ChunkSchema = None

logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))  # Batch size for embedding API
EMBED_CACHE_DIR = os.getenv("EMBED_CACHE_DIR", "./data/embed_cache")
CACHE_EXPIRY_SECONDS = float(os.getenv("EMBED_CACHE_EXPIRY_SECONDS", str(7 * 24 * 60 * 60)))  # One week
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Create cache directory
try:
    Path(EMBED_CACHE_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create embed cache dir {EMBED_CACHE_DIR}: {e}")

# Initialize embedding client (singleton)
_client = None


def _get_client() -> EmbeddingClient:
    """Get or create embedding client singleton."""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    
    Convenience method for embedding user queries during retrieval.
    
    Args:
        query: Query string to embed
        
    Returns:
        Single embedding vector (List[float])
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to embed_query")
        return []
    
    embeddings = embed_texts([query.strip()])
    if embeddings and len(embeddings) > 0:
        return embeddings[0]
    return []


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of text strings into vectors.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each is List[float])
    """
    if not texts:
        return []
    
    results = []
    n = len(texts)
    
    logger.debug(f"Embedding {n} texts in batches of {BATCH_SIZE}")
    
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        
        try:
            client = _get_client()
            vecs = client.embed(batch)
            
            # Validate embeddings
            if len(vecs) != len(batch):
                logger.error(f"Embedding count mismatch: expected {len(batch)}, got {len(vecs)}")
                # Fallback for missing embeddings
                for text in batch[len(vecs):]:
                    vecs.append(_fallback_vector(text))
            
            results.extend(vecs)
            
        except Exception as e:
            logger.exception(f"Embedding API error for batch {i//BATCH_SIZE + 1}: {e}")
            # Fallback: use hash-based embeddings
            logger.warning("Using fallback hash-based embeddings for failed batch")
            vecs = [_fallback_vector(t) for t in batch]
            results.extend(vecs)
        
        # Small delay to avoid overwhelming the API
        if i + BATCH_SIZE < n:
            time.sleep(0.01)
    
    return results


def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Any]:
    """
    Embed chunks and return ChunkSchema objects.
    
    Args:
        chunks: List of chunk dictionaries with:
            - chunk_id: str
            - text: str
            - chunk_index: int
            - meta: dict (optional, will be enriched)
            
    Returns:
        List of ChunkSchema objects with embeddings
    """
    if not chunks:
        return []
    
    # Extract texts for embedding
    texts = [chunk.get("text", "") for chunk in chunks]
    
    # Get embeddings
    embeddings = embed_texts(texts)
    
    if len(embeddings) != len(chunks):
        logger.error(
            f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks"
        )
        # Pad with fallback if needed
        while len(embeddings) < len(chunks):
            idx = len(embeddings)
            embeddings.append(_fallback_vector(chunks[idx].get("text", "")))
    
    # Create ChunkSchema objects or dicts
    chunk_schemas = []
    for chunk, embedding in zip(chunks, embeddings):
        try:
            # Ensure meta dict exists
            meta = chunk.get("meta", {}).copy()
            
            # Create ChunkSchema if available, otherwise use dict
            if ChunkSchema:
                chunk_schema = ChunkSchema(
                    chunk_id=chunk.get("chunk_id", ""),
                    text=chunk.get("text", ""),
                    embedding=embedding,
                    meta=meta
                )
            else:
                # Fallback to dict format
                chunk_schema = {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "text": chunk.get("text", ""),
                    "embedding": embedding,
                    "meta": meta
                }
            chunk_schemas.append(chunk_schema)
            
        except Exception as e:
            logger.exception(f"Error creating chunk schema for chunk {chunk.get('chunk_id')}: {e}")
            # Skip invalid chunks
            continue
    
    logger.info(f"Successfully embedded {len(chunk_schemas)}/{len(chunks)} chunks")
    return chunk_schemas


def _fallback_vector(text: str, dim: int = None) -> List[float]:
    """
    Generate a deterministic hash-based embedding as fallback.

    This is used when the embedding API fails. It's not semantically meaningful
    but provides a consistent vector representation.

    Args:
        text: Input text
        dim: Dimension of embedding (defaults to EMBEDDING_DIMENSION)

    Returns:
        List of floats representing a pseudo-embedding
    """
    # Use the configured embedding dimension, defaulting to 1536 for remote models
    if dim is None:
        # Check if we're using remote embeddings (which should be 1536)
        from .model import USE_REMOTE
        dim = 1536 if USE_REMOTE else EMBEDDING_DIMENSION

    h = abs(hash(text)) % (10**9)

    # Generate deterministic vector from hash
    vector = []
    for i in range(dim):
        # Use hash bits to generate values
        bit_shift = (h >> (i % 31)) % 100
        vector.append(bit_shift / 100.0)

    return vector

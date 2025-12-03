"""
Retriever - Perform semantic search in vector DB.

Purpose: Perform semantic search in vector DB
Input: A query embedding
Output: A list of RetrievedChunk objects
Used by: query_engine.py
"""
import logging
from typing import List, Optional

from vectorstore.vector_store import get_vector_store
from schema.retrieval_schema import RetrievedChunk

logger = logging.getLogger(__name__)


class Retriever:
    """
    Semantic search retriever for vector database.
    
    This class handles retrieval of similar chunks from the vector store
    based on query embeddings.
    """
    
    def __init__(self, vector_store=None, min_similarity: float = 0.0):
        """
        Initialize retriever.
        
        Args:
            vector_store: Vector store instance (default: get from factory)
            min_similarity: Minimum similarity score to include (0.0 to 1.0)
        """
        self.vector_store = vector_store or get_vector_store()
        self.min_similarity = min_similarity
        logger.info(f"Retriever initialized with min_similarity={min_similarity}")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks in vector database.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            min_similarity: Override instance min_similarity (optional)
            
        Returns:
            List of RetrievedChunk objects sorted by similarity (highest first)
        """
        if not query_embedding:
            logger.warning("Empty query embedding provided")
            return []
        
        if top_k <= 0:
            logger.warning(f"Invalid top_k={top_k}, using default=5")
            top_k = 5
        
        min_sim = min_similarity if min_similarity is not None else self.min_similarity
        
        try:
            # Search vector store
            results = self.vector_store.search(query_embedding, top_k=top_k)
            
            if not results:
                logger.debug("No results found in vector store")
                return []
            
            # Convert to RetrievedChunk objects
            retrieved_chunks = []
            for result in results:
                similarity = result.get("score", 0.0)
                
                # Filter by minimum similarity
                if similarity < min_sim:
                    continue
                
                chunk = RetrievedChunk(
                    text=result.get("text", ""),
                    similarity=float(similarity),
                    meta=result.get("meta", {}),
                    chunk_id=result.get("chunk_id")
                )
                retrieved_chunks.append(chunk)
            
            # Sort by similarity (highest first) - should already be sorted, but ensure it
            retrieved_chunks.sort(key=lambda x: x.similarity, reverse=True)
            
            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks "
                f"(requested top_k={top_k}, min_similarity={min_sim})"
            )
            
            return retrieved_chunks
            
        except Exception as e:
            logger.exception(f"Error during retrieval: {e}")
            return []
    
    def get_stats(self) -> dict:
        """Get vector store statistics."""
        try:
            return self.vector_store.get_stats()
        except Exception as e:
            logger.exception(f"Error getting stats: {e}")
            return {}


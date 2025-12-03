"""
Index Rebuilder - Wipe and rebuild vector database index.

Purpose: Wipes existing vector DB and re-runs ingestion
Steps:
  1. vector_store.clear()
  2. Run the entire ingestion pipeline again

Input: None
Output: Summary of reindexing operation
"""
import os
import logging
from typing import Optional, Dict, Any

from .ingest_pipeline import run_ingestion_pipeline
from vectorstore.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def rebuild_index(
    category: Optional[str] = None,
    min_posts: Optional[int] = None,
    force: bool = True,
    vector_store_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rebuild the entire vector database index.
    
    This function:
    1. Clears the existing vector store (if force=True)
    2. Runs the complete ingestion pipeline
    
    Args:
        category: Discourse category slug (defaults to env var)
        min_posts: Minimum number of posts to fetch (defaults to env var)
        force: If True, clear vector store before indexing (default: True)
        vector_store_type: "chroma" or "faiss" (defaults to env var)
        
    Returns:
        Dictionary with reindexing statistics
    """
    logger.info("=" * 60)
    logger.info("Starting index rebuild")
    logger.info("=" * 60)
    
    try:
        # Step 1: Clear vector store if requested
        if force:
            logger.info("Clearing existing vector store...")
            try:
                vector_store = get_vector_store(store_type=vector_store_type)
                vector_store.clear()
                logger.info("✓ Vector store cleared")
            except Exception as e:
                logger.exception(f"Error clearing vector store: {e}")
                # Continue anyway - ingestion will overwrite
        else:
            logger.info("Skipping vector store clear (force=False)")
        
        # Step 2: Run ingestion pipeline
        logger.info("Running ingestion pipeline...")
        result = run_ingestion_pipeline(
            category=category,
            min_posts=min_posts,
            vector_store_type=vector_store_type
        )
        
        # Add rebuild-specific metadata
        result["rebuild"] = True
        result["force_clear"] = force
        
        logger.info("=" * 60)
        logger.info("Index rebuild completed")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.exception(f"Fatal error in index rebuild: {e}")
        return {
            "status": "error",
            "error": str(e),
            "rebuild": True
        }


# Alias for backward compatibility
run_full_reindex = rebuild_index


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Rebuild vector database index")
    parser.add_argument("--category", type=str, default=None, help="Discourse category slug")
    parser.add_argument("--min-posts", type=int, default=None, help="Minimum posts to fetch")
    parser.add_argument("--force", action="store_true", default=True, help="Clear vector store before indexing")
    parser.add_argument("--no-force", dest="force", action="store_false", help="Don't clear vector store")
    parser.add_argument("--store-type", type=str, default=None, choices=["chroma", "faiss"], help="Vector store type")
    
    args = parser.parse_args()
    
    result = rebuild_index(
        category=args.category,
        min_posts=args.min_posts,
        force=args.force,
        vector_store_type=args.store_type
    )
    
    print("\nRebuild Result:")
    print(result)

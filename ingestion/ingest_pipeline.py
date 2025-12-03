"""
Ingestion Pipeline Controller - Orchestrates the entire ingestion pipeline.

Purpose: Orchestrate the entire ingestion pipeline step-by-step
Flow: fetch_discourse → html_parser → cleaner → chunker → embedder → vector_store
Input: None (invoked manually or on server bootstrap)
Output: Logs and final summary
"""
import os
import logging
import time
from typing import List, Dict, Any, Optional

from .fetch_discourse import fetch_discourse_posts
from .html_parser import html_to_text
from .cleaner import normalize_text
from .chunker import split_into_chunks
from embeddings.embedder import embed_chunks
from vectorstore.vector_store import get_vector_store, insert_chunks

logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = int(os.getenv("INGESTION_BATCH_SIZE", "100"))  # Process posts in batches
MIN_POST_LENGTH = int(os.getenv("MIN_POST_LENGTH_WORDS", "8"))  # Skip posts shorter than this


def run_ingestion_pipeline(
    category: Optional[str] = None,
    min_posts: Optional[int] = None,
    vector_store_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete ingestion pipeline.
    
    Steps:
    1. Fetch posts from Discourse API
    2. Parse HTML to text
    3. Clean and normalize text
    4. Split into chunks
    5. Generate embeddings
    6. Insert into vector store
    
    Args:
        category: Discourse category slug (defaults to env var)
        min_posts: Minimum number of posts to fetch (defaults to env var)
        vector_store_type: "chroma" or "faiss" (defaults to env var)
        
    Returns:
        Dictionary with statistics:
        {
            "status": "ok",
            "posts_fetched": 500,
            "posts_processed": 480,
            "chunks_created": 1200,
            "chunks_inserted": 1200,
            "duration_seconds": 45.2,
            "errors": []
        }
    """
    start_time = time.time()
    stats = {
        "status": "ok",
        "posts_fetched": 0,
        "posts_processed": 0,
        "chunks_created": 0,
        "chunks_inserted": 0,
        "duration_seconds": 0,
        "errors": []
    }
    
    try:
        # Step 1: Fetch posts from Discourse
        logger.info("=" * 60)
        logger.info("Starting ingestion pipeline")
        logger.info("=" * 60)
        
        logger.info("Step 1/6: Fetching posts from Discourse...")
        posts = fetch_discourse_posts(category=category, min_posts=min_posts)
        stats["posts_fetched"] = len(posts)
        logger.info(f"✓ Fetched {len(posts)} posts")
        
        if not posts:
            logger.warning("No posts fetched, aborting pipeline")
            stats["status"] = "no_posts"
            return stats
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = get_vector_store(store_type=vector_store_type)
        logger.info(f"✓ Vector store initialized: {type(vector_store).__name__}")
        
        # Process posts in batches
        all_chunks = []
        processed_count = 0
        
        logger.info(f"Step 2-5/6: Processing {len(posts)} posts...")
        
        for i, post in enumerate(posts):
            try:
                # Step 2: Parse HTML
                html_content = post.get("content", "")
                if not html_content:
                    logger.debug(f"Skipping post {post.get('id')}: no content")
                    continue
                
                parsed = html_to_text(html_content)
                text = parsed.get("text", "")
                
                if not text or len(text.split()) < MIN_POST_LENGTH:
                    logger.debug(f"Skipping post {post.get('id')}: too short")
                    continue
                
                # Step 3: Clean text
                cleaned_text = normalize_text(text)
                
                if not cleaned_text or len(cleaned_text.split()) < MIN_POST_LENGTH:
                    logger.debug(f"Skipping post {post.get('id')}: too short after cleaning")
                    continue
                
                # Step 4: Chunk text
                chunks = split_into_chunks(cleaned_text)
                
                if not chunks:
                    logger.debug(f"Skipping post {post.get('id')}: no chunks created")
                    continue
                
                # Enrich chunks with metadata
                for chunk in chunks:
                    chunk["meta"] = {
                        "post_id": str(post.get("id", "")),
                        "topic_id": str(post.get("topic_id", "")),
                        "url": post.get("url", ""),
                        "title": post.get("title", ""),
                        "timestamp": post.get("created_at", ""),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "author": post.get("username") or post.get("name", ""),
                    }
                
                all_chunks.extend(chunks)
                processed_count += 1
                
                # Log progress
                if (i + 1) % 50 == 0:
                    logger.info(f"  Processed {i + 1}/{len(posts)} posts, created {len(all_chunks)} chunks so far...")
                
            except Exception as e:
                error_msg = f"Error processing post {post.get('id')}: {e}"
                logger.exception(error_msg)
                stats["errors"].append(error_msg)
                continue
        
        stats["posts_processed"] = processed_count
        stats["chunks_created"] = len(all_chunks)
        logger.info(f"✓ Processed {processed_count} posts, created {len(all_chunks)} chunks")
        
        if not all_chunks:
            logger.warning("No chunks created, aborting pipeline")
            stats["status"] = "no_chunks"
            return stats
        
        # Step 5: Generate embeddings (in batches)
        logger.info("Step 5/6: Generating embeddings...")
        embedded_chunks = embed_chunks(all_chunks)
        logger.info(f"✓ Generated embeddings for {len(embedded_chunks)} chunks")
        
        if len(embedded_chunks) != len(all_chunks):
            logger.warning(
                f"Embedding count mismatch: {len(embedded_chunks)} embedded vs {len(all_chunks)} chunks"
            )
        
        # Step 6: Insert into vector store (in batches)
        logger.info("Step 6/6: Inserting chunks into vector store...")
        
        inserted_total = 0
        batch_num = 0
        
        for i in range(0, len(embedded_chunks), BATCH_SIZE):
            batch = embedded_chunks[i:i + BATCH_SIZE]
            batch_num += 1
            
            try:
                result = insert_chunks(vector_store, batch)
                inserted = result.get("inserted", 0)
                inserted_total += inserted
                
                logger.debug(f"  Batch {batch_num}: inserted {inserted} chunks")
                
            except Exception as e:
                error_msg = f"Error inserting batch {batch_num}: {e}"
                logger.exception(error_msg)
                stats["errors"].append(error_msg)
                continue
        
        stats["chunks_inserted"] = inserted_total
        
        # Persist vector store
        try:
            vector_store.persist()
        except Exception as e:
            logger.warning(f"Failed to persist vector store: {e}")
        
        duration = time.time() - start_time
        stats["duration_seconds"] = round(duration, 2)
        
        # Final summary
        logger.info("=" * 60)
        logger.info("Ingestion pipeline completed successfully!")
        logger.info(f"  Posts fetched: {stats['posts_fetched']}")
        logger.info(f"  Posts processed: {stats['posts_processed']}")
        logger.info(f"  Chunks created: {stats['chunks_created']}")
        logger.info(f"  Chunks inserted: {stats['chunks_inserted']}")
        logger.info(f"  Duration: {stats['duration_seconds']}s")
        if stats["errors"]:
            logger.warning(f"  Errors encountered: {len(stats['errors'])}")
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.exception(f"Fatal error in ingestion pipeline: {e}")
        stats["status"] = "error"
        stats["error"] = str(e)
        stats["duration_seconds"] = round(time.time() - start_time, 2)
        return stats


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run pipeline
    result = run_ingestion_pipeline()
    print("\nPipeline Result:")
    print(result)


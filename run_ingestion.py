"""
Simple script to run the ingestion pipeline.

Usage:
    python run_ingestion.py
    python run_ingestion.py --min-posts 10
    python run_ingestion.py --rebuild
"""
import os
import sys
import argparse
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from ingestion.ingest_pipeline import run_ingestion_pipeline
from ingestion.index_rebuilder import rebuild_index

def main():
    parser = argparse.ArgumentParser(description="Run Discourse RAG Ingestion Pipeline")
    parser.add_argument("--min-posts", type=int, default=None, 
                       help="Minimum number of posts to fetch (default: from env or 500)")
    parser.add_argument("--category", type=str, default=None,
                       help="Discourse category slug (default: from env)")
    parser.add_argument("--rebuild", action="store_true",
                       help="Rebuild index (clear and re-ingest)")
    parser.add_argument("--store-type", type=str, choices=["chroma", "faiss"], default=None,
                       help="Vector store type (default: from env)")
    
    args = parser.parse_args()
    
    # Check required environment variables
    if not os.getenv("DISCOURSE_BASE_URL") or not os.getenv("DISCOURSE_API_KEY"):
        print("⚠️  WARNING: DISCOURSE_BASE_URL or DISCOURSE_API_KEY not set!")
        print("\nPlease set these in your .env file or environment:")
        print("  DISCOURSE_BASE_URL=https://your-discourse-instance.com")
        print("  DISCOURSE_API_KEY=your_api_key")
        print("  DISCOURSE_API_USERNAME=system")
        print("\nWithout these, the pipeline cannot fetch data from Discourse.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("=" * 60)
    print("Discourse RAG Ingestion Pipeline")
    print("=" * 60)
    print()
    
    if args.rebuild:
        print("🔄 Rebuilding index (will clear existing data)...")
        result = rebuild_index(
            category=args.category,
            min_posts=args.min_posts,
            force=True,
            vector_store_type=args.store_type
        )
    else:
        print("▶️  Running ingestion pipeline...")
        result = run_ingestion_pipeline(
            category=args.category,
            min_posts=args.min_posts,
            vector_store_type=args.store_type
        )
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Posts fetched: {result.get('posts_fetched', 0)}")
    print(f"Posts processed: {result.get('posts_processed', 0)}")
    print(f"Chunks created: {result.get('chunks_created', 0)}")
    print(f"Chunks inserted: {result.get('chunks_inserted', 0)}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors encountered: {len(result['errors'])}")
        for err in result['errors'][:5]:  # Show first 5
            print(f"  - {err[:100]}")
    
    if result.get('status') == 'ok':
        print("\n✅ Pipeline completed successfully!")
        
        # Verify vector store
        try:
            from vectorstore.vector_store import get_vector_store
            store = get_vector_store(store_type=args.store_type)
            stats = store.get_stats()
            print(f"\n📊 Vector Store Stats:")
            print(f"  Type: {stats.get('store_type', 'unknown')}")
            print(f"  Chunks stored: {stats.get('count', 'unknown')}")
        except Exception as e:
            print(f"\n⚠️  Could not verify vector store: {e}")
    else:
        print(f"\n❌ Pipeline failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()


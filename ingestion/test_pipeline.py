"""
Test script for ingestion pipeline.

This script provides various test functions to verify the ingestion pipeline works correctly.
Run with: python -m ingestion.test_pipeline
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.fetch_discourse import fetch_discourse_posts
from ingestion.html_parser import html_to_text
from ingestion.cleaner import normalize_text
from ingestion.chunker import split_into_chunks
from embeddings.embedder import embed_chunks
from ingestion.ingest_pipeline import run_ingestion_pipeline
from ingestion.index_rebuilder import rebuild_index
from vectorstore.vector_store import get_vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_html_parser():
    """Test HTML parser component."""
    print("\n" + "="*60)
    print("TEST 1: HTML Parser")
    print("="*60)
    
    test_html = """
    <p>This is a <b>test</b> paragraph.</p>
    <p>Here's a <a href="https://example.com">link</a>.</p>
    <pre><code>print("Hello World")</code></pre>
    """
    
    result = html_to_text(test_html)
    
    print(f"Input HTML length: {len(test_html)}")
    print(f"Output text length: {len(result['text'])}")
    print(f"Extracted text: {result['text'][:100]}...")
    print(f"Links found: {result['links']}")
    print(f"Has code: {result['has_code']}")
    print(f"Code blocks: {len(result['code_blocks'])}")
    
    assert result['text'], "Text should not be empty"
    assert len(result['links']) > 0, "Should find links"
    assert result['has_code'], "Should detect code blocks"
    
    print("✓ HTML Parser test passed!")
    return True


def test_cleaner():
    """Test text cleaner component."""
    print("\n" + "="*60)
    print("TEST 2: Text Cleaner")
    print("="*60)
    
    test_text = """
    Hello   World
    
    
    
    This is a test.
    
    Regards,
    Test User
    """
    
    cleaned = normalize_text(test_text)
    
    print(f"Input length: {len(test_text)}")
    print(f"Output length: {len(cleaned)}")
    print(f"Cleaned text: {cleaned}")
    
    assert cleaned, "Cleaned text should not be empty"
    assert "Regards" not in cleaned, "Should remove signatures"
    assert "  " not in cleaned, "Should collapse whitespace"
    
    print("✓ Text Cleaner test passed!")
    return True


def test_chunker():
    """Test text chunker component."""
    print("\n" + "="*60)
    print("TEST 3: Text Chunker")
    print("="*60)
    
    # Create a longer text for chunking
    test_text = " ".join([f"This is sentence {i}." for i in range(50)])
    
    chunks = split_into_chunks(test_text, chunk_size=100, overlap=20)
    
    print(f"Input text length: {len(test_text)}")
    print(f"Number of chunks created: {len(chunks)}")
    print(f"First chunk: {chunks[0]['text'][:80]}...")
    print(f"Last chunk: {chunks[-1]['text'][:80]}...")
    
    assert len(chunks) > 0, "Should create at least one chunk"
    assert all('chunk_id' in c for c in chunks), "All chunks should have chunk_id"
    assert all('text' in c for c in chunks), "All chunks should have text"
    assert all('chunk_index' in c for c in chunks), "All chunks should have chunk_index"
    
    # Check overlap
    if len(chunks) > 1:
        chunk1_words = set(chunks[0]['text'].split())
        chunk2_words = set(chunks[1]['text'].split())
        overlap_words = chunk1_words & chunk2_words
        print(f"Overlap words between chunks: {len(overlap_words)}")
    
    print("✓ Text Chunker test passed!")
    return True


def test_embedder():
    """Test embedder component."""
    print("\n" + "="*60)
    print("TEST 4: Embedder")
    print("="*60)
    
    test_chunks = [
        {
            "chunk_id": "test_chunk_1",
            "text": "This is a test chunk for embedding.",
            "chunk_index": 0,
            "meta": {}
        },
        {
            "chunk_id": "test_chunk_2",
            "text": "Another test chunk with different content.",
            "chunk_index": 1,
            "meta": {}
        }
    ]
    
    embedded = embed_chunks(test_chunks)
    
    print(f"Input chunks: {len(test_chunks)}")
    print(f"Output embedded chunks: {len(embedded)}")
    
    assert len(embedded) == len(test_chunks), "Should embed all chunks"
    
    for i, emb in enumerate(embedded):
        has_embedding = False
        if hasattr(emb, 'embedding'):
            has_embedding = bool(emb.embedding)
            emb_dim = len(emb.embedding) if emb.embedding else 0
        elif isinstance(emb, dict):
            has_embedding = bool(emb.get('embedding'))
            emb_dim = len(emb.get('embedding', []))
        else:
            has_embedding = hasattr(emb, '__dict__') and 'embedding' in emb.__dict__
            if has_embedding:
                emb_dim = len(getattr(emb, 'embedding', []))
            else:
                emb_dim = 0
        
        print(f"  Chunk {i+1}: embedding_dim={emb_dim}")
        assert has_embedding, f"Chunk {i+1} should have embedding"
        assert emb_dim > 0, f"Chunk {i+1} embedding should not be empty"
    
    print("✓ Embedder test passed!")
    return True


def test_vector_store():
    """Test vector store operations."""
    print("\n" + "="*60)
    print("TEST 5: Vector Store")
    print("="*60)
    
    try:
        store = get_vector_store()
        print(f"✓ Vector store initialized: {type(store).__name__}")
        
        # Test stats
        stats = store.get_stats()
        print(f"  Store stats: {stats}")
        
        # Test search (should work even with empty store)
        test_vector = [0.1] * 384  # Dummy vector
        results = store.search(test_vector, top_k=5)
        print(f"  Search returned {len(results)} results")
        
        print("✓ Vector Store test passed!")
        return True
    except Exception as e:
        print(f"✗ Vector Store test failed: {e}")
        logger.exception("Vector store test error")
        return False


def test_fetch_discourse_small():
    """Test fetching a small number of posts (requires API credentials)."""
    print("\n" + "="*60)
    print("TEST 6: Fetch Discourse (Small Sample)")
    print("="*60)
    
    # Check if credentials are set
    if not os.getenv("DISCOURSE_BASE_URL") or not os.getenv("DISCOURSE_API_KEY"):
        print("⚠ Skipping: DISCOURSE_BASE_URL and DISCOURSE_API_KEY not set")
        print("  Set these environment variables to test Discourse fetching")
        return None
    
    try:
        # Fetch just 5 posts for testing
        posts = fetch_discourse_posts(min_posts=5)
        
        print(f"✓ Fetched {len(posts)} posts")
        if posts:
            print(f"  First post ID: {posts[0].get('id')}")
            print(f"  First post title: {posts[0].get('title', 'N/A')[:50]}")
            print(f"  First post content length: {len(posts[0].get('content', ''))}")
        
        assert len(posts) > 0, "Should fetch at least one post"
        
        print("✓ Fetch Discourse test passed!")
        return True
    except Exception as e:
        print(f"✗ Fetch Discourse test failed: {e}")
        logger.exception("Fetch discourse test error")
        return False


def test_full_pipeline_small():
    """Test the full pipeline with a small number of posts."""
    print("\n" + "="*60)
    print("TEST 7: Full Pipeline (Small Sample)")
    print("="*60)
    
    # Check if credentials are set
    if not os.getenv("DISCOURSE_BASE_URL") or not os.getenv("DISCOURSE_API_KEY"):
        print("⚠ Skipping: DISCOURSE_BASE_URL and DISCOURSE_API_KEY not set")
        return None
    
    try:
        # Run pipeline with just 10 posts
        result = run_ingestion_pipeline(min_posts=10)
        
        print(f"\nPipeline Result:")
        print(f"  Status: {result.get('status')}")
        print(f"  Posts fetched: {result.get('posts_fetched', 0)}")
        print(f"  Posts processed: {result.get('posts_processed', 0)}")
        print(f"  Chunks created: {result.get('chunks_created', 0)}")
        print(f"  Chunks inserted: {result.get('chunks_inserted', 0)}")
        print(f"  Duration: {result.get('duration_seconds', 0)}s")
        
        if result.get('errors'):
            print(f"  Errors: {len(result['errors'])}")
            for err in result['errors'][:3]:  # Show first 3 errors
                print(f"    - {err[:100]}")
        
        assert result.get('status') == 'ok', "Pipeline should complete successfully"
        assert result.get('chunks_inserted', 0) > 0, "Should insert at least one chunk"
        
        print("✓ Full Pipeline test passed!")
        return True
    except Exception as e:
        print(f"✗ Full Pipeline test failed: {e}")
        logger.exception("Full pipeline test error")
        return False


def test_with_mock_data():
    """Test pipeline components with mock data (no API calls)."""
    print("\n" + "="*60)
    print("TEST 8: Pipeline with Mock Data")
    print("="*60)
    
    # Create mock post data
    mock_posts = [
        {
            "id": 1,
            "topic_id": 10,
            "post_number": 1,
            "content": "<p>This is a test post about <b>Python programming</b>.</p><p>It contains multiple paragraphs.</p>",
            "created_at": "2024-01-01T00:00:00Z",
            "username": "testuser",
            "name": "Test User",
            "title": "Test Topic",
            "slug": "test-topic",
            "url": "https://example.com/t/test-topic/10/1"
        },
        {
            "id": 2,
            "topic_id": 10,
            "post_number": 2,
            "content": "<p>Another post with <a href='https://example.com'>a link</a>.</p>",
            "created_at": "2024-01-02T00:00:00Z",
            "username": "testuser2",
            "name": "Test User 2",
            "title": "Test Topic",
            "slug": "test-topic",
            "url": "https://example.com/t/test-topic/10/2"
        }
    ]
    
    all_chunks = []
    
    for post in mock_posts:
        # Parse HTML
        parsed = html_to_text(post["content"])
        text = parsed["text"]
        
        # Clean
        cleaned = normalize_text(text)
        
        # Chunk
        chunks = split_into_chunks(cleaned)
        
        # Add metadata
        for chunk in chunks:
            chunk["meta"] = {
                "post_id": str(post["id"]),
                "topic_id": str(post["topic_id"]),
                "url": post["url"],
                "title": post["title"],
                "timestamp": post["created_at"],
                "chunk_index": chunk.get("chunk_index", 0),
                "author": post["username"]
            }
        
        all_chunks.extend(chunks)
    
    # Embed
    embedded = embed_chunks(all_chunks)
    
    print(f"Mock posts processed: {len(mock_posts)}")
    print(f"Chunks created: {len(all_chunks)}")
    print(f"Chunks embedded: {len(embedded)}")
    
    # Verify structure
    for emb in embedded:
        if hasattr(emb, 'chunk_id'):
            print(f"  Chunk: {emb.chunk_id}, meta: {emb.meta.get('post_id')}")
        elif isinstance(emb, dict):
            print(f"  Chunk: {emb.get('chunk_id')}, meta: {emb.get('meta', {}).get('post_id')}")
    
    assert len(embedded) > 0, "Should create embedded chunks"
    
    print("✓ Mock data pipeline test passed!")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("RUNNING ALL TESTS")
    print("="*60)
    
    results = {}
    
    # Component tests (no API required)
    results['html_parser'] = test_html_parser()
    results['cleaner'] = test_cleaner()
    results['chunker'] = test_chunker()
    results['embedder'] = test_embedder()
    results['vector_store'] = test_vector_store()
    results['mock_data'] = test_with_mock_data()
    
    # API-dependent tests (may skip if credentials not set)
    results['fetch_discourse'] = test_fetch_discourse_small()
    results['full_pipeline'] = test_full_pipeline_small()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else "✗ FAIL" if result is False else "⊘ SKIP"
        print(f"  {test_name:20s} {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ingestion pipeline")
    parser.add_argument("--test", type=str, help="Run specific test (html_parser, cleaner, chunker, embedder, vector_store, fetch, pipeline, mock, all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.test:
        test_map = {
            "html_parser": test_html_parser,
            "cleaner": test_cleaner,
            "chunker": test_chunker,
            "embedder": test_embedder,
            "vector_store": test_vector_store,
            "fetch": test_fetch_discourse_small,
            "pipeline": test_full_pipeline_small,
            "mock": test_with_mock_data,
            "all": run_all_tests
        }
        
        if args.test in test_map:
            test_map[args.test]()
        else:
            print(f"Unknown test: {args.test}")
            print(f"Available tests: {', '.join(test_map.keys())}")
            sys.exit(1)
    else:
        # Run all tests by default
        sys.exit(run_all_tests())


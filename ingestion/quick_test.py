"""
Quick test script - Minimal test to verify pipeline works.

Usage: python -m ingestion.quick_test
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def quick_test():
    """Run a quick end-to-end test with mock data."""
    print("Running quick test...")
    
    # Test 1: Import all modules
    print("\n1. Testing imports...")
    try:
        from ingestion.html_parser import html_to_text
        from ingestion.cleaner import normalize_text
        from ingestion.chunker import split_into_chunks
        from embeddings.embedder import embed_chunks
        from vectorstore.vector_store import get_vector_store
        print("   ✓ All imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Test 2: Test pipeline components
    print("\n2. Testing pipeline components...")
    
    # HTML parsing
    html = "<p>Test <b>content</b> with <a href='https://example.com'>link</a>.</p>"
    parsed = html_to_text(html)
    assert parsed['text'], "HTML parsing failed"
    print("   ✓ HTML parser works")
    
    # Text cleaning
    dirty = "Hello   World\n\n\nTest"
    clean = normalize_text(dirty)
    assert clean, "Text cleaning failed"
    print("   ✓ Text cleaner works")
    
    # Chunking
    long_text = " ".join([f"Sentence {i}." for i in range(30)])
    chunks = split_into_chunks(long_text, chunk_size=50, overlap=10)
    assert len(chunks) > 0, "Chunking failed"
    print(f"   ✓ Chunker works (created {len(chunks)} chunks)")
    
    # Embedding
    test_chunks = [{"chunk_id": "1", "text": "Test chunk", "chunk_index": 0, "meta": {}}]
    embedded = embed_chunks(test_chunks)
    assert len(embedded) > 0, "Embedding failed"
    print("   ✓ Embedder works")
    
    # Vector store
    try:
        store = get_vector_store()
        stats = store.get_stats()
        print(f"   ✓ Vector store works ({stats.get('store_type', 'unknown')})")
    except Exception as e:
        print(f"   ⚠ Vector store warning: {e}")
    
    # Test 3: Check environment
    print("\n3. Checking environment...")
    required_vars = ["DISCOURSE_BASE_URL", "DISCOURSE_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        print(f"   ⚠ Missing env vars: {', '.join(missing)}")
        print("   (API tests will be skipped)")
    else:
        print("   ✓ Environment variables set")
    
    print("\n" + "="*60)
    print("Quick test completed!")
    print("="*60)
    print("\nTo run full tests:")
    print("  python -m ingestion.test_pipeline")
    print("\nTo test with real data:")
    print("  python -m ingestion.ingest_pipeline")
    
    return True

if __name__ == "__main__":
    quick_test()


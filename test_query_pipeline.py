"""
Test script for query pipeline.

Tests the complete RAG query pipeline end-to-end.
"""
import os
import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from schema.ask_request import AskRequest
from rag.query_engine import get_query_engine
from rag.retriever import Retriever
from embeddings.embedder import embed_query
from vectorstore.vector_store import get_vector_store

def test_components():
    """Test individual components."""
    print("=" * 60)
    print("Testing Query Pipeline Components")
    print("=" * 60)
    print()
    
    # Test 1: Vector Store
    print("1. Testing Vector Store...")
    try:
        store = get_vector_store()
        stats = store.get_stats()
        print(f"   ✓ Vector store: {stats.get('store_type', 'unknown')}")
        print(f"   ✓ Chunks in store: {stats.get('count', 'unknown')}")
    except Exception as e:
        print(f"   ✗ Vector store error: {e}")
        return False
    print()
    
    # Test 2: Embedder
    print("2. Testing Query Embedding...")
    try:
        test_query = "What is Python?"
        embedding = embed_query(test_query)
        print(f"   ✓ Query embedded: {len(embedding)} dimensions")
    except Exception as e:
        print(f"   ✗ Embedding error: {e}")
        return False
    print()
    
    # Test 3: Retriever
    print("3. Testing Retriever...")
    try:
        retriever = Retriever()
        chunks = retriever.search(embedding, top_k=3)
        print(f"   ✓ Retrieved {len(chunks)} chunks")
        if chunks:
            print(f"   ✓ Top similarity: {chunks[0].similarity:.3f}")
    except Exception as e:
        print(f"   ✗ Retrieval error: {e}")
        return False
    print()
    
    return True

def test_full_pipeline():
    """Test full RAG pipeline."""
    print("=" * 60)
    print("Testing Full RAG Pipeline")
    print("=" * 60)
    print()
    
    # Check if LLM is configured
    if not os.getenv("AIPIPE_BASE_URL") or not os.getenv("AIPIPE_API_KEY"):
        print("⚠️  LLM not configured (AIPIPE_BASE_URL/AIPIPE_API_KEY)")
        print("   Skipping full pipeline test (requires LLM)")
        return False
    
    try:
        # Create request
        request = AskRequest(
            query="What is Python programming?",
            top_k=3
        )
        
        print(f"Query: {request.query}")
        print(f"Top K: {request.top_k}")
        print()
        
        # Get query engine
        query_engine = get_query_engine()
        
        # Answer question
        print("Running query pipeline...")
        response = query_engine.answer_question(request)
        
        print()
        print("=" * 60)
        print("RESPONSE")
        print("=" * 60)
        print(f"Answer: {response.answer[:200]}...")
        print(f"Sources: {len(response.sources)}")
        print(f"Latency: {response.latency_ms:.0f}ms")
        print(f"Model: {response.model_used or 'unknown'}")
        print()
        
        if response.sources:
            print("Sources:")
            for i, source in enumerate(response.sources[:3], 1):
                print(f"  {i}. {source.title} (similarity: {source.similarity:.3f})")
                print(f"     URL: {source.url}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    
    # Test components first
    if not test_components():
        print("\n❌ Component tests failed. Fix issues before testing full pipeline.")
        sys.exit(1)
    
    print()
    
    # Test full pipeline
    if test_full_pipeline():
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Full pipeline test skipped or failed (check LLM configuration)")


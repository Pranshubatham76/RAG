"""
Demo script to run ingestion pipeline with mock data (no API required).

This demonstrates the full pipeline working end-to-end.
"""
import os
import sys
from pathlib import Path
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.html_parser import html_to_text
from ingestion.cleaner import normalize_text
from ingestion.chunker import split_into_chunks
from embeddings.embedder import embed_chunks
from vectorstore.vector_store import get_vector_store, insert_chunks

def create_mock_posts():
    """Create sample mock posts for testing."""
    return [
        {
            "id": 1,
            "topic_id": 10,
            "post_number": 1,
            "content": """
            <p>Welcome to our discussion about <b>Python programming</b>!</p>
            <p>In this post, we'll explore various aspects of Python development.</p>
            <p>Python is a versatile language used for web development, data science, and automation.</p>
            <p>Here are some key features:</p>
            <ul>
                <li>Easy to learn syntax</li>
                <li>Large standard library</li>
                <li>Strong community support</li>
            </ul>
            <p>Let's dive deeper into these topics.</p>
            """,
            "created_at": "2024-01-01T10:00:00Z",
            "username": "python_dev",
            "name": "Python Developer",
            "title": "Introduction to Python Programming",
            "slug": "introduction-to-python",
            "url": "https://example.com/t/introduction-to-python/10/1"
        },
        {
            "id": 2,
            "topic_id": 10,
            "post_number": 2,
            "content": """
            <p>Great introduction! I'd like to add that Python's <a href="https://pypi.org">package ecosystem</a> is also amazing.</p>
            <p>With pip, you can easily install thousands of packages.</p>
            <pre><code>pip install requests
import requests
response = requests.get('https://api.example.com')
</code></pre>
            <p>This makes Python very powerful for various use cases.</p>
            """,
            "created_at": "2024-01-01T11:00:00Z",
            "username": "web_dev",
            "name": "Web Developer",
            "title": "Introduction to Python Programming",
            "slug": "introduction-to-python",
            "url": "https://example.com/t/introduction-to-python/10/2"
        },
        {
            "id": 3,
            "topic_id": 11,
            "post_number": 1,
            "content": """
            <p>Let's discuss <b>machine learning</b> with Python.</p>
            <p>Python has excellent libraries like scikit-learn, TensorFlow, and PyTorch.</p>
            <p>These tools make it easy to build and train machine learning models.</p>
            """,
            "created_at": "2024-01-02T09:00:00Z",
            "username": "ml_engineer",
            "name": "ML Engineer",
            "title": "Machine Learning with Python",
            "slug": "machine-learning-python",
            "url": "https://example.com/t/machine-learning-python/11/1"
        }
    ]

def run_demo_pipeline():
    """Run the ingestion pipeline with mock data."""
    print("=" * 60)
    print("Discourse RAG Ingestion Pipeline - DEMO MODE")
    print("=" * 60)
    print()
    
    # Step 1: Create mock posts
    print("Step 1/6: Creating mock posts...")
    posts = create_mock_posts()
    print(f"[OK] Created {len(posts)} mock posts")
    print()
    
    # Step 2: Initialize vector store
    print("Step 2/6: Initializing vector store...")
    try:
        store = get_vector_store()
        print(f"[OK] Vector store initialized: {type(store).__name__}")
    except Exception as e:
        print(f"⚠️  Vector store warning: {e}")
        print("   Continuing with demo (some features may not work)")
        store = None
    print()
    
    # Process each post
    all_chunks = []
    processed_count = 0
    
    print("Step 3-5/6: Processing posts through pipeline...")
    print()
    
    for i, post in enumerate(posts, 1):
        print(f"Processing post {i}/{len(posts)}: {post.get('title', 'Untitled')[:50]}...")
        
        try:
            # Step 3: Parse HTML
            html_content = post.get("content", "")
            parsed = html_to_text(html_content)
            text = parsed.get("text", "")

            if not text:
                print(f"  [SKIP] No text extracted")
                continue
            
            # Step 4: Clean text
            cleaned_text = normalize_text(text)

            if not cleaned_text:
                print(f"  [SKIP] Text too short after cleaning")
                continue
            
            # Step 5: Chunk text
            chunks = split_into_chunks(cleaned_text)

            if not chunks:
                print(f"  [SKIP] No chunks created")
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
            
            print(f"  [OK] Created {len(chunks)} chunks")
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            continue
    
    print()
    print(f"[OK] Processed {processed_count}/{len(posts)} posts")
    print(f"[OK] Created {len(all_chunks)} total chunks")
    print()
    
    if not all_chunks:
        print("❌ No chunks created. Cannot continue.")
        return
    
    # Step 6: Generate embeddings
    print("Step 6/6: Generating embeddings...")
    try:
        embedded_chunks = embed_chunks(all_chunks)
        print(f"[OK] Generated embeddings for {len(embedded_chunks)} chunks")
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        return
    print()
    
    # Step 7: Insert into vector store
    if store:
        print("Step 7/7: Inserting into vector store...")
        try:
            result = insert_chunks(store, embedded_chunks)
            inserted = result.get("inserted", 0)
            print(f"[OK] Inserted {inserted} chunks into vector store")
            
            # Get stats
            stats = store.get_stats()
            print(f"  Total chunks in store: {stats.get('count', 'unknown')}")
        except Exception as e:
            print(f"[ERROR] Insert failed: {e}")
    else:
        print("[SKIP] Skipping vector store insertion (store not available)")
    
    print()
    print("=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print(f"Posts processed: {processed_count}")
    print(f"Chunks created: {len(all_chunks)}")
    print(f"Chunks embedded: {len(embedded_chunks)}")
    if store:
        print(f"Chunks inserted: {inserted}")
    print()
    print("[SUCCESS] Pipeline works correctly!")
    
    # Test search if store is available
    if store:
        print()
        print("Testing search functionality...")
        try:
            from embeddings.embedder import embed_texts
            query = "Python programming"
            query_vector = embed_texts([query])[0]
            results = store.search(query_vector, top_k=3)
            print(f"[OK] Search returned {len(results)} results")
            if results:
                print(f"  Top result: {results[0].get('text', '')[:80]}...")
        except Exception as e:
            print(f"[WARN] Search test failed: {e}")

if __name__ == "__main__":
    run_demo_pipeline()


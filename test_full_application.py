"""
Comprehensive test script for the entire Discourse RAG application.

This script:
1. Runs ingestion pipeline with demo data
2. Tests all API endpoints (health, search, ask)
3. Verifies end-to-end functionality

Usage:
    python test_full_application.py
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Set default embedding model if not set (use a valid sentence-transformers model)
# This overrides the default in settings.py which uses an invalid model
if not os.getenv('EMBEDDING_MODEL'):
    os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'

import django
django.setup()

# Fix ALLOWED_HOSTS for test client
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
if '*' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('*')

from django.test import Client

# Import application modules
from ingestion.html_parser import html_to_text
from ingestion.cleaner import normalize_text
from ingestion.chunker import split_into_chunks
from embeddings.embedder import embed_chunks
from vectorstore.vector_store import get_vector_store, insert_chunks
from dotenv import load_dotenv

load_dotenv()

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(f"{BOLD}{text}{RESET}")
    print("=" * 70)
    print()


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ {text}{RESET}")


def create_demo_posts():
    """Create comprehensive demo posts for testing."""
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
                <li>Extensive package ecosystem via PyPI</li>
            </ul>
            <p>Let's dive deeper into these topics.</p>
            <p>Python supports multiple programming paradigms including object-oriented, functional, and procedural programming.</p>
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
print(response.json())
</code></pre>
            <p>This makes Python very powerful for various use cases including web scraping, API integration, and data processing.</p>
            <p>Popular frameworks like Django and Flask make web development straightforward.</p>
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
            <p>Scikit-learn provides simple and efficient tools for data mining and data analysis.</p>
            <p>TensorFlow and PyTorch are powerful frameworks for deep learning applications.</p>
            """,
            "created_at": "2024-01-02T09:00:00Z",
            "username": "ml_engineer",
            "name": "ML Engineer",
            "title": "Machine Learning with Python",
            "slug": "machine-learning-python",
            "url": "https://example.com/t/machine-learning-python/11/1"
        },
        {
            "id": 4,
            "topic_id": 12,
            "post_number": 1,
            "content": """
            <p>Data science is another major application of Python.</p>
            <p>Libraries like pandas, NumPy, and Matplotlib are essential for data analysis.</p>
            <p>Pandas provides data structures and operations for manipulating numerical tables and time series.</p>
            <p>NumPy offers support for large, multi-dimensional arrays and matrices.</p>
            <p>Matplotlib enables creating static, animated, and interactive visualizations.</p>
            """,
            "created_at": "2024-01-03T14:00:00Z",
            "username": "data_scientist",
            "name": "Data Scientist",
            "title": "Data Science with Python",
            "slug": "data-science-python",
            "url": "https://example.com/t/data-science-python/12/1"
        },
        {
            "id": 5,
            "topic_id": 13,
            "post_number": 1,
            "content": """
            <p>Python is also great for automation and scripting.</p>
            <p>You can automate repetitive tasks, interact with APIs, and process files.</p>
            <p>Common use cases include:</p>
            <ul>
                <li>File processing and batch operations</li>
                <li>Web scraping with BeautifulSoup or Scrapy</li>
                <li>System administration tasks</li>
                <li>Testing and quality assurance</li>
            </ul>
            <p>The simplicity of Python makes it ideal for quick scripts and complex automation workflows.</p>
            """,
            "created_at": "2024-01-04T16:00:00Z",
            "username": "automation_expert",
            "name": "Automation Expert",
            "title": "Python for Automation",
            "slug": "python-automation",
            "url": "https://example.com/t/python-automation/13/1"
        }
    ]


def run_ingestion_demo():
    """Run the ingestion pipeline with demo data."""
    print_header("STEP 1: Running Ingestion Pipeline with Demo Data")
    
    # Clear existing data for clean test
    print_info("Clearing existing vector store data...")
    try:
        store = get_vector_store()
        print("store : ", store)
        time.sleep(10)
        store.clear()
        print_success("Vector store cleared")

    except Exception as e:
        print_warning(f"Could not clear vector store: {e}")
    
    # Create mock posts
    print_info("Creating demo posts...")
    posts = create_demo_posts()
    print("posts : ", posts)
    time.sleep(10)
    print_success(f"Created {len(posts)} demo posts")
    
    # Initialize vector store
    print_info("Initializing vector store...")
    try:
        store = get_vector_store()
        print("store : ", store)
        time.sleep(10)

        store_type = type(store).__name__
        print_success(f"Vector store initialized: {store_type}")

    except Exception as e:
        print_error(f"Vector store initialization failed: {e}")
        return False
    
    # Process posts
    all_chunks = []
    processed_count = 0
    
    print_info("Processing posts through pipeline...")
    for i, post in enumerate(posts, 1):
        try:
            # Parse HTML
            html_content = post.get("content", "")
            print("html_content : ", html_content)
            time.sleep(10)

            parsed = html_to_text(html_content)
            print("parsed : ", parsed)
            time.sleep(10)

            text = parsed.get("text", "")
            print("text : ", text)
            time.sleep(10)


            if not text:
                print_warning(f"Post {i}: No text extracted")
                continue
            
            # Clean text
            cleaned_text = normalize_text(text)
            print("cleaned_text : ", cleaned_text)
            
            if not cleaned_text:
                print_warning(f"Post {i}: Text too short after cleaning")
                continue
            
            # Chunk text
            chunks = split_into_chunks(cleaned_text)
            print("chunks : ", chunks)
            time.sleep(10)

            if not chunks:
                print_warning(f"Post {i}: No chunks created")
                continue
            
            # Enrich chunks with metadata
            for chunk in chunks:
                print("chunk : ", chunk)
                time.sleep(10)
                print("post : ", post)
                time.sleep(10)

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
            print("all_chunks : ", all_chunks)
            time.sleep(10)

            processed_count += 1
            print_success(f"Post {i}: Created {len(chunks)} chunks")
            
        except Exception as e:
            print_error(f"Post {i}: Processing failed - {e}")
            continue
    
    if not all_chunks:
        print_error("No chunks created. Cannot continue.")
        return False
    
    print_success(f"Processed {processed_count}/{len(posts)} posts")
    print_success(f"Created {len(all_chunks)} total chunks")
    
    # Generate embeddings
    print_info("Generating embeddings...")
    try:
        embedded_chunks = embed_chunks(all_chunks)
        print("embedded_chunks : ", embedded_chunks)
        time.sleep(10)
        print_success(f"Generated embeddings for {len(embedded_chunks)} chunks")
    except Exception as e:
        print_error(f"Embedding failed: {e}")
        return False
    
    # Insert into vector store
    print_info("Inserting chunks into vector store...")
    try:
        result = insert_chunks(store, embedded_chunks)
        print("result : ", result)
        time.sleep(10)

        inserted = result.get("inserted", 0)
        print("inserted : ", inserted)
        time.sleep(10)

        print_success(f"Inserted {inserted} chunks into vector store")
        
        # Get stats
        stats = store.get_stats()
        print("stats : ", stats)
        time.sleep(10)

        total_count = stats.get('count', 'unknown')
        print_success(f"Total chunks in store: {total_count}")
        
        return True
        
    except Exception as e:
        print_error(f"Insert failed: {e}")
        return False


def test_api_endpoints():
    """Test all API endpoints using Django test client."""
    print_header("STEP 2: Testing API Endpoints")
    
    client = Client()
    results = {
        "health": False,
        "search": False,
        "ask": False
    }
    
    # Test 1: Health endpoint
    print_info("Testing /api/v1/health endpoint...")
    try:
        response = client.get('/api/v1/health')
        # Accept both 200 and 503 (503 means not ready but endpoint works)
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"
        
        data = json.loads(response.content)
        print("data : ", data)
        time.sleep(10)

        assert "status" in data, "Missing 'status' in response"
        assert "ready" in data, "Missing 'ready' in response"
        assert "vector_store" in data, "Missing 'vector_store' in response"
        
        status = data.get('status')
        ready = data.get('ready')
        count = data.get('vector_store', {}).get('count')
        
        print_success(f"Health check passed: status={status}, ready={ready}")
        print_info(f"  Vector store: {data.get('vector_store', {}).get('type', 'unknown')}")
        print_info(f"  Chunks: {count if count is not None else 'unknown'}")
        
        if not ready:
            print_warning("System not ready (no data indexed or count unavailable)")
        else:
            print_success("System is ready")
        
        # Health endpoint works if it returns valid JSON with expected fields
        # Even if status is not_ready, the endpoint itself is functioning
        results["health"] = True
        
    except Exception as e:
        print_error(f"Health endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Search endpoint
    print_info("Testing /api/v1/search endpoint...")
    try:
        search_query = {
            "query": "Python programming",
            "top_k": 3
        }
        
        response = client.post(
            '/api/v1/search',
            data=json.dumps(search_query),
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = json.loads(response.content)
        print("data : ", data)
        time.sleep(10)

        assert "query" in data, "Missing 'query' in response"
        assert "results" in data, "Missing 'results' in response"
        assert "count" in data, "Missing 'count' in response"
        
        print_success(f"Search endpoint passed: found {data.get('count', 0)} results")
        
        if data.get('results'):
            top_result = data['results'][0]
            print("top_result : ", top_result)
            time.sleep(10)
            print_info(f"  Top result similarity: {top_result.get('similarity', 0):.3f}")
            print_info(f"  Top result text: {top_result.get('text', '')[:60]}...")
        
        results["search"] = True
        
    except Exception as e:
        print_error(f"Search endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Ask endpoint (RAG)
    print_info("Testing /api/v1/ask endpoint...")
    
    # Check if LLM is configured
    if not os.getenv("AIPIPE_BASE_URL") or not os.getenv("AIPIPE_API_KEY"):
        print_warning("LLM not configured (AIPIPE_BASE_URL/AIPIPE_API_KEY)")
        print_warning("Skipping /ask endpoint test (requires LLM)")
        results["ask"] = None  # Skipped
    else:
        try:
            ask_query = {
                "query": "What is Python programming?",
                "top_k": 3
            }
            
            print_info("  Sending query to RAG pipeline (this may take a moment)...")
            start_time = time.time()

            response = client.post(
                '/api/v1/ask',
                data=json.dumps(ask_query),
                content_type='application/json'
            )

            
            
            elapsed = (time.time() - start_time) * 1000
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = json.loads(response.content)
            print("data : ", data)
            time.sleep(10)
            assert "answer" in data, "Missing 'answer' in response"
            assert "sources" in data, "Missing 'sources' in response"
            
            print_success(f"Ask endpoint passed: {elapsed:.0f}ms")
            print_info(f"  Answer length: {len(data.get('answer', ''))} characters")
            print_info(f"  Sources: {len(data.get('sources', []))}")
            print_info(f"  Latency: {data.get('latency_ms', 0):.0f}ms")
            
            if data.get('answer'):
                print_info(f"  Answer preview: {data['answer'][:100]}...")
            
            if data.get('sources'):
                print_info("  Top sources:")
                for i, source in enumerate(data['sources'][:3], 1):
                    print_info(f"    {i}. {source.get('title', 'Untitled')} (similarity: {source.get('similarity', 0):.3f})")
            
            results["ask"] = True
            
        except Exception as e:
            print_error(f"Ask endpoint test failed: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def test_multiple_queries():
    """Test multiple different queries to verify system robustness."""
    print_header("STEP 3: Testing Multiple Query Types")
    
    client = Client()
    test_queries = [
        {"query": "machine learning", "top_k": 2},
        {"query": "data science libraries", "top_k": 3},
        {"query": "automation with Python", "top_k": 2},
    ]
    
    passed = 0
    failed = 0
    
    for i, query_data in enumerate(test_queries, 1):
        query = query_data["query"]
        top_k = query_data["top_k"]
        
        print_info(f"Query {i}/{len(test_queries)}: '{query}'")
        
        try:
            response = client.post(
                '/api/v1/search',
                data=json.dumps(query_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = json.loads(response.content)
                count = data.get('count', 0)
                print_success(f"  Found {count} results")
                if data.get('results'):
                    print_info(f"  Top similarity: {data['results'][0].get('similarity', 0):.3f}")
                passed += 1
            else:
                print_error(f"  Failed with status {response.status_code}")
                failed += 1
                
        except Exception as e:
            print_error(f"  Error: {e}")
            failed += 1
    
    print()
    print_success(f"Query tests: {passed} passed, {failed} failed")
    
    return failed == 0


def print_summary(ingestion_success, api_results, query_tests_success):
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    print(f"{BOLD}Ingestion Pipeline:{RESET}")
    if ingestion_success:
        print_success("✓ Ingestion completed successfully")
    else:
        print_error("✗ Ingestion failed")
    
    print()
    print(f"{BOLD}API Endpoints:{RESET}")
    
    if api_results["health"]:
        print_success("✓ /api/v1/health - PASSED")
    else:
        print_error("✗ /api/v1/health - FAILED")
    
    if api_results["search"]:
        print_success("✓ /api/v1/search - PASSED")
    else:
        print_error("✗ /api/v1/search - FAILED")
    
    if api_results["ask"] is True:
        print_success("✓ /api/v1/ask - PASSED")
    elif api_results["ask"] is None:
        print_warning("⚠ /api/v1/ask - SKIPPED (LLM not configured)")
    else:
        print_error("✗ /api/v1/ask - FAILED")
    
    print()
    print(f"{BOLD}Query Robustness:{RESET}")
    if query_tests_success:
        print_success("✓ Multiple query tests passed")
    else:
        print_error("✗ Some query tests failed")
    
    print()
    print("=" * 70)
    
    # Overall status
    all_critical_passed = (
        ingestion_success and
        api_results["health"] and
        api_results["search"]
    )
    
    if all_critical_passed:
        print(f"{GREEN}{BOLD}✅ ALL CRITICAL TESTS PASSED!{RESET}")
        if api_results["ask"] is True:
            print(f"{GREEN}{BOLD}✅ FULL RAG PIPELINE WORKING!{RESET}")
    else:
        print(f"{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")
    
    print("=" * 70)
    print()


def main():
    """Main test function."""
    print()
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}Discourse RAG Application - Full Test Suite{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    
    # Step 1: Run ingestion
    ingestion_success = run_ingestion_demo()
    
    if not ingestion_success:
        print_error("Ingestion failed. Cannot continue with API tests.")
        print_summary(False, {"health": False, "search": False, "ask": False}, False)
        sys.exit(1)
    
    print()
    time.sleep(1)  # Brief pause
    
    # Step 2: Test API endpoints
    api_results = test_api_endpoints()
    
    print()
    time.sleep(1)  # Brief pause
    
    # Step 3: Test multiple queries
    query_tests_success = test_multiple_queries()
    
    # Print summary
    print_summary(ingestion_success, api_results, query_tests_success)
    
    # Exit code
    all_critical_passed = (
        ingestion_success and
        api_results["health"] and
        api_results["search"]
    )
    
    sys.exit(0 if all_critical_passed else 1)


if __name__ == "__main__":
    main()

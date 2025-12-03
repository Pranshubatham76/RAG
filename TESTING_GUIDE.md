# Testing Guide for Ingestion Pipeline

This guide explains how to test the ingestion pipeline to verify it works correctly.

## Prerequisites

1. **Environment Variables**: Set up your `.env` file or environment variables:
   ```bash
   DISCOURSE_BASE_URL=https://your-discourse-instance.com
   DISCOURSE_API_KEY=your_api_key
   DISCOURSE_API_USERNAME=system
   DISCOURSE_CATEGORY=reading-club
   VECTOR_STORE_TYPE=chroma  # or faiss
   ```

2. **Dependencies**: Ensure all required packages are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. **NLTK Data** (for chunker):
   ```python
   import nltk
   nltk.download('punkt')
   ```

## Quick Test (Recommended First Step)

Run the automated test suite:

```bash
python -m ingestion.test_pipeline
```

This will run all component tests and verify the pipeline works end-to-end.

## Component-Level Testing

### 1. Test Individual Components

You can test each component individually:

```bash
# Test HTML parser
python -m ingestion.test_pipeline --test html_parser

# Test text cleaner
python -m ingestion.test_pipeline --test cleaner

# Test chunker
python -m ingestion.test_pipeline --test chunker

# Test embedder
python -m ingestion.test_pipeline --test embedder

# Test vector store
python -m ingestion.test_pipeline --test vector_store

# Test with mock data (no API calls)
python -m ingestion.test_pipeline --test mock
```

### 2. Test with Real API (Requires Credentials)

```bash
# Test Discourse fetching (small sample)
python -m ingestion.test_pipeline --test fetch

# Test full pipeline (10 posts)
python -m ingestion.test_pipeline --test pipeline
```

## Manual Testing Steps

### Step 1: Test HTML Parser

```python
from ingestion.html_parser import html_to_text

html = "<p>Hello <b>World</b></p><a href='https://example.com'>Link</a>"
result = html_to_text(html)
print(result)
# Should output: {'text': 'Hello World\nLink', 'links': ['https://example.com'], ...}
```

### Step 2: Test Text Cleaner

```python
from ingestion.cleaner import normalize_text

dirty_text = "Hello   World\n\n\nTest"
clean = normalize_text(dirty_text)
print(clean)
# Should output: "Hello World\nTest"
```

### Step 3: Test Chunker

```python
from ingestion.chunker import split_into_chunks

long_text = " ".join([f"Sentence {i}." for i in range(100)])
chunks = split_into_chunks(long_text, chunk_size=50, overlap=10)
print(f"Created {len(chunks)} chunks")
```

### Step 4: Test Embedder

```python
from embeddings.embedder import embed_chunks

chunks = [
    {"chunk_id": "1", "text": "Test chunk", "chunk_index": 0, "meta": {}}
]
embedded = embed_chunks(chunks)
print(f"Embedded {len(embedded)} chunks")
```

### Step 5: Test Vector Store

```python
from vectorstore.vector_store import get_vector_store

store = get_vector_store()
stats = store.get_stats()
print(f"Store stats: {stats}")
```

## Full Pipeline Testing

### Test with Small Sample (Recommended First)

```python
from ingestion.ingest_pipeline import run_ingestion_pipeline

# Test with just 10 posts
result = run_ingestion_pipeline(min_posts=10)

print(f"Status: {result['status']}")
print(f"Posts processed: {result['posts_processed']}")
print(f"Chunks inserted: {result['chunks_inserted']}")
```

Or via command line:

```bash
python -c "from ingestion.ingest_pipeline import run_ingestion_pipeline; print(run_ingestion_pipeline(min_posts=10))"
```

### Test Full Pipeline

```python
from ingestion.ingest_pipeline import run_ingestion_pipeline

# Run with default settings (500 posts)
result = run_ingestion_pipeline()

if result['status'] == 'ok':
    print("✓ Pipeline completed successfully!")
    print(f"  Chunks inserted: {result['chunks_inserted']}")
else:
    print(f"✗ Pipeline failed: {result.get('error')}")
```

### Test Index Rebuild

```python
from ingestion.index_rebuilder import rebuild_index

# Rebuild index (clears and re-ingests)
result = rebuild_index(force=True, min_posts=50)

print(f"Rebuild status: {result['status']}")
```

Or via command line:

```bash
python -m ingestion.index_rebuilder --force --min-posts 50
```

## Verification Steps

### 1. Check Vector Store Contents

```python
from vectorstore.vector_store import get_vector_store

store = get_vector_store()
stats = store.get_stats()
print(f"Total chunks in store: {stats.get('count', 'unknown')}")

# Test search
test_query = [0.1] * 384  # Dummy vector (adjust dimension)
results = store.search(test_query, top_k=5)
print(f"Search returned {len(results)} results")
```

### 2. Verify Chunk Structure

```python
# After running pipeline, check if chunks have correct structure
from vectorstore.vector_store import get_vector_store

store = get_vector_store()
results = store.search([0.1] * 384, top_k=1)

if results:
    chunk = results[0]
    print(f"Chunk ID: {chunk.get('chunk_id')}")
    print(f"Text: {chunk.get('text', '')[:100]}...")
    print(f"Meta: {chunk.get('meta', {})}")
    
    # Verify required metadata fields
    meta = chunk.get('meta', {})
    assert 'post_id' in meta, "Missing post_id"
    assert 'topic_id' in meta, "Missing topic_id"
    assert 'url' in meta, "Missing url"
```

### 3. Check Logs

The pipeline logs detailed information. Check logs for:
- Number of posts fetched
- Number of posts processed
- Number of chunks created
- Number of chunks inserted
- Any errors encountered

## Common Issues and Solutions

### Issue: "DISCOURSE_BASE_URL not set"
**Solution**: Set environment variables in `.env` file or export them:
```bash
export DISCOURSE_BASE_URL=https://your-instance.com
export DISCOURSE_API_KEY=your_key
```

### Issue: "NLTK punkt not found"
**Solution**: Download NLTK data:
```python
import nltk
nltk.download('punkt')
```

### Issue: "ChromaDB/FAISS import error"
**Solution**: Install required packages:
```bash
pip install chromadb  # or
pip install faiss-cpu
```

### Issue: "Embedding API error"
**Solution**: 
- Check if embedding model is available
- Verify `EMBEDDING_MODEL` environment variable
- Check network connection if using remote embeddings

### Issue: "No chunks inserted"
**Solution**:
- Check if posts have sufficient content (MIN_POST_LENGTH_WORDS)
- Verify text cleaning is not removing all content
- Check logs for filtering reasons

## Performance Testing

### Test with Different Batch Sizes

```python
import os
os.environ['INGESTION_BATCH_SIZE'] = '50'  # Smaller batches
os.environ['EMBEDDING_BATCH_SIZE'] = '16'  # Smaller embedding batches

from ingestion.ingest_pipeline import run_ingestion_pipeline
result = run_ingestion_pipeline(min_posts=100)
```

### Monitor Resource Usage

```bash
# On Linux/Mac
python -m ingestion.ingest_pipeline &
top -p $!

# Or use htop
htop
```

## Integration Testing

### Test End-to-End Flow

1. **Clear existing index**:
   ```python
   from vectorstore.vector_store import get_vector_store
   store = get_vector_store()
   store.clear()
   ```

2. **Run ingestion**:
   ```python
   from ingestion.ingest_pipeline import run_ingestion_pipeline
   result = run_ingestion_pipeline(min_posts=20)
   ```

3. **Verify search works**:
   ```python
   from embeddings.embedder import embed_texts
   from vectorstore.vector_store import get_vector_store
   
   # Create query embedding
   query_text = "test query"
   query_vector = embed_texts([query_text])[0]
   
   # Search
   store = get_vector_store()
   results = store.search(query_vector, top_k=5)
   
   print(f"Found {len(results)} results")
   for r in results:
       print(f"  Score: {r['score']:.3f}, Text: {r['text'][:50]}...")
   ```

## Expected Output

When running the test suite, you should see:

```
============================================================
RUNNING ALL TESTS
============================================================

============================================================
TEST 1: HTML Parser
============================================================
✓ HTML Parser test passed!

============================================================
TEST 2: Text Cleaner
============================================================
✓ Text Cleaner test passed!

...

============================================================
TEST SUMMARY
============================================================
  html_parser          ✓ PASS
  cleaner             ✓ PASS
  chunker             ✓ PASS
  embedder            ✓ PASS
  vector_store        ✓ PASS
  mock_data           ✓ PASS
  fetch_discourse     ✓ PASS
  full_pipeline       ✓ PASS

Total: 8 passed, 0 failed, 0 skipped

🎉 All tests passed!
```

## Next Steps

After verifying the pipeline works:

1. **Run full ingestion** with your desired number of posts
2. **Monitor logs** for any issues
3. **Verify search functionality** with real queries
4. **Check vector store stats** to confirm data is stored correctly

For production deployment, consider:
- Setting up scheduled reindexing
- Monitoring pipeline health
- Setting up alerts for failures
- Optimizing batch sizes for your infrastructure


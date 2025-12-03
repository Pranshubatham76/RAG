# Quick Test Guide - Ingestion Pipeline

## Fastest Way to Test (No API Required)

```bash
# Quick test - verifies all components work
python -m ingestion.quick_test
```

This will test:
- ✓ All imports work
- ✓ HTML parser
- ✓ Text cleaner  
- ✓ Chunker
- ✓ Embedder
- ✓ Vector store initialization

## Full Test Suite

```bash
# Run all tests (skips API tests if credentials not set)
python -m ingestion.test_pipeline
```

Or run specific tests:

```bash
# Test individual components
python -m ingestion.test_pipeline --test html_parser
python -m ingestion.test_pipeline --test cleaner
python -m ingestion.test_pipeline --test chunker
python -m ingestion.test_pipeline --test embedder
python -m ingestion.test_pipeline --test vector_store

# Test with mock data (no API calls)
python -m ingestion.test_pipeline --test mock

# Test with real API (requires credentials)
python -m ingestion.test_pipeline --test fetch      # Test fetching
python -m ingestion.test_pipeline --test pipeline   # Test full pipeline
```

## Test with Real Data (Small Sample)

```bash
# Test with just 10 posts
python -c "from ingestion.ingest_pipeline import run_ingestion_pipeline; print(run_ingestion_pipeline(min_posts=10))"
```

Or:

```python
from ingestion.ingest_pipeline import run_ingestion_pipeline

result = run_ingestion_pipeline(min_posts=10)
print(result)
```

## Verify Results

After running ingestion, verify the vector store:

```python
from vectorstore.vector_store import get_vector_store

store = get_vector_store()
stats = store.get_stats()
print(f"Chunks in store: {stats.get('count', 'unknown')}")

# Test search
from embeddings.embedder import embed_texts
query_vector = embed_texts(["test query"])[0]
results = store.search(query_vector, top_k=5)
print(f"Search results: {len(results)}")
```

## Expected Output

When everything works, you should see:

```
✓ All imports successful
✓ HTML parser works
✓ Text cleaner works
✓ Chunker works (created X chunks)
✓ Embedder works
✓ Vector store works (chroma/faiss)
```

## Troubleshooting

**Import errors?**
- Make sure you're in the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

**NLTK errors?**
```python
import nltk
nltk.download('punkt')
```

**Vector store errors?**
- Install chromadb: `pip install chromadb`
- Or install faiss: `pip install faiss-cpu`

**API errors?**
- Set environment variables:
  ```bash
  export DISCOURSE_BASE_URL=https://your-instance.com
  export DISCOURSE_API_KEY=your_key
  ```

For detailed testing instructions, see `TESTING_GUIDE.md`.


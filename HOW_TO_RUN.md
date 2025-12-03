# How to Run the Ingestion Pipeline

## Quick Start

### Option 1: Demo Mode (No API Required) ✅

Test the full pipeline with mock data:

```bash
python run_ingestion_demo.py
```

This will:
- Create 3 sample posts
- Process them through the entire pipeline
- Generate embeddings
- Store in vector database
- Test search functionality

**Perfect for testing without API credentials!**

### Option 2: Real Pipeline (Requires API)

Run with real Discourse data:

```bash
# Small test (5 posts)
python run_ingestion.py --min-posts 5

# Normal run (500 posts - default)
python run_ingestion.py

# Rebuild index (clear and re-ingest)
python run_ingestion.py --rebuild

# Custom category
python run_ingestion.py --category your-category --min-posts 100
```

## What You'll See

The pipeline will show:
- ✅ Posts fetched from Discourse
- ✅ Posts processed
- ✅ Chunks created
- ✅ Embeddings generated
- ✅ Chunks inserted into vector store
- ✅ Final statistics

## Verify It Worked

After running, check the vector store:


```python
from vectorstore.vector_store import get_vector_store

store = get_vector_store()
stats = store.get_stats()
print(f"Chunks in store: {stats.get('count', 'unknown')}")

# Test search
from embeddings.embedder import embed_texts
query_vector = embed_texts(["your search query"])[0]
results = store.search(query_vector, top_k=5)
print(f"Found {len(results)} results")
```

## Troubleshooting

### API Returns 403 Error
- Check your `DISCOURSE_API_KEY` is correct
- Verify `DISCOURSE_API_USERNAME` has proper permissions
- Make sure the category exists and is accessible

### Vector Store Issues
- Try using FAISS instead: `--store-type faiss`
- Check disk space for ChromaDB persistence

### No Posts Fetched
- Verify category slug is correct
- Check API credentials
- Try a different category

## Files Created

- `run_ingestion.py` - Main pipeline runner
- `run_ingestion_demo.py` - Demo with mock data
- `ingestion/ingest_pipeline.py` - Core pipeline logic
- `ingestion/index_rebuilder.py` - Rebuild functionality

## Next Steps

After ingestion:
1. Verify data in vector store
2. Test search functionality
3. Integrate with your RAG application
4. Set up scheduled reindexing if needed


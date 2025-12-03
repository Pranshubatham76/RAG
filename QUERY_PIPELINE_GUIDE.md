# Query Pipeline - Complete Guide

## Overview

The query pipeline performs **real-time RAG (Retrieval-Augmented Generation)** when a user submits a question. It:

1. Converts user query → embedding
2. Retrieves similar documents from vector DB
3. Constructs RAG prompt
4. Sends to LLM (via AIPipe → OpenRouter)
5. Returns final answer + citations to frontend

## Architecture

```
Frontend
    │
    ▼
/api/v1/ask  → AskRequest
    │
    ▼
query_engine.py
    │
    ├─ embedder.embed_query(query)
    │
    ├─ retriever.search(embedding)
    │
    ├─ prompt_builder.create_prompt()
    │
    ├─ llm_client.generate()
    │
    ▼
AskResponse
    │
    ▼
Frontend UI (Final answer + sources)
```

## Components

### 1. Schemas (`schema/`)

- **`ask_request.py`**: Validates incoming user query
- **`ask_response.py`**: Structures final API response
- **`retrieval_schema.py`**: `RetrievedChunk` for search results

### 2. RAG Components (`rag/`)

- **`query_engine.py`**: Main orchestrator (coordinates entire pipeline)
- **`retriever.py`**: Semantic search in vector DB
- **`prompt_builder.py`**: Constructs RAG prompts
- **`llm_client.py`**: LLM API client (AIPipe → OpenRouter)

### 3. API Routes (`api/routes/`)

- **`ask.py`**: Main RAG endpoint (`POST /api/v1/ask`)
- **`search.py`**: Search-only endpoint (`POST /api/v1/search`)
- **`health.py`**: Health check (`GET /api/v1/health`)

## API Endpoints

### POST `/api/v1/ask`

Main RAG inference endpoint.

**Request:**
```json
{
  "query": "What is the reading club about?",
  "top_k": 3,
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "The reading club is a community discussion forum...",
  "sources": [
    {
      "url": "https://discourse.example.com/t/topic/123",
      "title": "Reading Club Introduction",
      "similarity": 0.85,
      "post_id": "12",
      "topic_id": "5"
    }
  ],
  "latency_ms": 1532.5,
  "chunks_retrieved": 3,
  "model_used": "gpt-4"
}
```

### POST `/api/v1/search`

Search vector DB only (no LLM, for debugging).

**Request:**
```json
{
  "query": "Python programming",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "Python programming",
  "results": [
    {
      "text": "...",
      "similarity": 0.82,
      "meta": {...}
    }
  ],
  "count": 5
}
```

### GET `/api/v1/health`

Check system health and readiness.

**Response:**
```json
{
  "status": "healthy",
  "ready": true,
  "vector_store": {
    "type": "chroma",
    "count": 1200,
    "available": true
  }
}
```

## Environment Variables

Required for query pipeline:

```bash
# LLM Configuration
AIPIPE_BASE_URL=https://your-aipipe-instance.com
AIPIPE_API_KEY=your_api_key
LLM_MODEL=openai/gpt-4o-mini  # Optional, default
LLM_MAX_TOKENS=1000  # Optional, default
LLM_TEMPERATURE=0.7  # Optional, default

# Vector Store (already configured from ingestion)
VECTOR_STORE_TYPE=chroma  # or faiss
VECTOR_STORE_PATH=./data/vectorstore
```

## Usage Examples

### Python

```python
from schema.ask_request import AskRequest
from rag.query_engine import get_query_engine

# Create request
request = AskRequest(
    query="What is Python?",
    top_k=5
)

# Get query engine
engine = get_query_engine()

# Answer question
response = engine.answer_question(request)

print(response.answer)
print(f"Sources: {len(response.sources)}")
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the reading club about?",
    "top_k": 3
  }'
```

### JavaScript/Fetch

```javascript
const response = await fetch('http://localhost:8000/api/v1/ask', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'What is the reading club about?',
    top_k: 3
  })
});

const data = await response.json();
console.log(data.answer);
console.log(data.sources);
```

## Testing

### Test Components

```bash
python test_query_pipeline.py
```

This will:
1. Test vector store connection
2. Test query embedding
3. Test retrieval
4. Test full pipeline (if LLM configured)

### Test via API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Search only
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Python", "top_k": 3}'

# Full RAG query
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "top_k": 3}'
```

## Connection with Ingestion Pipeline

### Ingestion Pipeline
- Builds the vector DB: `Clean text → chunks → embeddings → vector DB`
- Stores chunks with metadata

### Query Pipeline
- Reads from the same vector DB: `Use embeddings + metadata for retrieval`
- Uses the same `vector_store.py` interface

### Shared Components
- `vectorstore/vector_store.py` - Both use same interface
- `embeddings/embedder.py` - Same embedding model
- `schema/retrieval_schema.py` - Shared schemas

## Error Handling

The pipeline handles:
- Empty queries
- No results from vector store
- LLM API failures
- Invalid requests
- Timeout errors

All errors return appropriate HTTP status codes and error messages.

## Performance

Typical latency breakdown:
- Query embedding: ~50-100ms
- Vector search: ~10-50ms
- Prompt building: ~5ms
- LLM generation: ~500-2000ms
- **Total: ~600-2200ms**

## Troubleshooting

### "No chunks retrieved"
- Check if ingestion pipeline has run
- Verify vector store has data: `GET /api/v1/health`
- Check vector store path and permissions

### "LLM generation failed"
- Verify `AIPIPE_BASE_URL` and `AIPIPE_API_KEY` are set
- Check network connectivity
- Verify API key has proper permissions

### "Vector store not available"
- Check `VECTOR_STORE_TYPE` environment variable
- Verify ChromaDB/FAISS is installed
- Check vector store path exists

## Next Steps

1. Run ingestion pipeline to populate vector DB
2. Configure LLM API credentials
3. Test with `/api/v1/health` to verify readiness
4. Start making queries via `/api/v1/ask`
5. Integrate with frontend


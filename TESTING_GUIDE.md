# Testing Guide - Discourse RAG Application

## Summary

✅ **Sample data has been successfully indexed!**
- 8 sample Discourse posts created
- 8 chunks generated and embedded
- All chunks inserted into ChromaDB vector store
- Vector store count: **8 chunks**

## What Was Done

1. ✅ Created sample Discourse posts (8 posts covering reading club topics)
2. ✅ Ran ingestion pipeline with sample data
3. ✅ Fixed vector store count issue
4. ✅ Verified data is in vector store

## How to Test the Application

### Step 1: Start Backend Server

Open a terminal and run:
```bash
# Activate virtual environment (if using one)
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Start Django server
python manage.py runserver
```

The backend will be available at: `http://localhost:8000`

### Step 2: Start Frontend Server

Open a **new terminal** and run:
```bash
cd frontend
npm start
```

The frontend will be available at: `http://localhost:3000`

### Step 3: Test Backend Endpoints

You can test the backend using the provided script:
```bash
python test_endpoints_with_data.py
```

Or test manually using curl:

**Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**Search Endpoint:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is the reading club?\", \"top_k\": 3}"
```

**Ask Endpoint:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is the reading club?\", \"top_k\": 3}"
```

### Step 4: Test Frontend

1. Open your browser and go to: `http://localhost:3000`
2. Check the health indicator - it should show "Ready (8 chunks)"
3. Try the following queries in the "Ask Question" tab:
   - "What is the reading club?"
   - "What book are we reading this month?"
   - "What are the benefits of joining?"
   - "How do we select books?"
   - "What are the discussion guidelines?"

4. Try the "Search Chunks" tab with queries like:
   - "reading club"
   - "book discussion"
   - "meeting schedule"

## Expected Results

### Health Endpoint
Should return:
```json
{
  "status": "healthy",
  "ready": true,
  "vector_store": {
    "type": "chroma",
    "count": 8,
    "available": true
  }
}
```

### Search Endpoint
Should return results with:
- `query`: Your search query
- `count`: Number of results (up to top_k)
- `results`: Array of chunks with:
  - `text`: Chunk text
  - `similarity`: Similarity score (0-1)
  - `chunk_id`: Chunk identifier
  - `meta`: Metadata (url, title, post_id, etc.)

### Ask Endpoint
Should return:
- `answer`: AI-generated answer based on retrieved chunks
- `sources`: Array of source citations
- `latency_ms`: Processing time
- `chunks_retrieved`: Number of chunks used

## Sample Data Topics

The indexed sample data includes:
1. Welcome to the Reading Club
2. Monthly Book Selection (The Great Gatsby)
3. Discussion Guidelines
4. Benefits of Joining
5. Book Selection Process
6. Quarterly Meeting Schedule
7. Tips for Book Discussions
8. New Members Welcome

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify Django dependencies are installed
- Check for errors in the terminal

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/settings.py`
- Verify proxy setting in `frontend/package.json` is `http://localhost:8000`

### No search results
- Verify vector store has data: Check health endpoint
- Ensure data was indexed: Run `python test_with_sample_data.py` again if needed

### LLM errors in Ask endpoint
- Check if AIPIPE credentials are configured (optional - search will still work)
- The ask endpoint may return an error if LLM is not configured, but search should work

## Files Created/Modified

1. `test_with_sample_data.py` - Script to index sample data
2. `test_endpoints_with_data.py` - Script to test backend endpoints
3. `test_connection.py` - Original connection test script
4. `frontend/src/components/SearchTab.jsx` - Created missing component
5. `frontend/src/components/QueryTab.jsx` - Fixed to use `chunk_text` instead of `text`
6. `vectorstore/chroma_store.py` - Fixed `get_stats()` method

## Next Steps

1. Start both servers (backend and frontend)
2. Test queries in the frontend UI
3. Verify data flows correctly from backend to frontend
4. Check that all fields are displayed correctly


# Discourse RAG Assistant

A Retrieval-Augmented Generation (RAG) assistant for Discourse forums, built with Django backend and React frontend.

## Features

- **Question Answering**: Ask questions about indexed Discourse content and get AI-powered answers with sources
- **Vector Search**: Debug tool for searching vector chunks without LLM generation
- **Health Monitoring**: Real-time backend health status and system readiness
- **Responsive UI**: Modern React interface with Material-UI components

## Architecture

- **Backend**: Django REST API with ChromaDB vector storage
- **Frontend**: React.js with Material-UI
- **Embeddings**: Sentence Transformers
- **LLM**: OpenAI GPT models via APIPE
- **Vector Store**: ChromaDB (with FAISS alternative)

## API Endpoints

- `GET /api/v1/health` - System health check
- `POST /api/v1/ask` - Main RAG query endpoint
- `POST /api/v1/search` - Vector search debugging

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- pip and npm

### Backend Setup

1. **Clone and navigate to project directory**
   ```bash
   cd discourse_rag_assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirement.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DISCOURSE_BASE_URL=your_discourse_url
   DISCOURSE_API_KEY=your_api_key
   DISCOURSE_API_USERNAME=your_username
   AIPIPE_BASE_URL=your_ai_pipe_url
   AIPIPE_API_KEY=your_ai_pipe_key
   ```

5. **Run Django migrations**
   ```bash
   python manage.py migrate
   ```

6. **Index Discourse data** (optional, if not already done)
   ```bash
   python manage.py shell -c "from ingestion.build_index import build_index; build_index()"
   ```

7. **Start Django server**
   ```bash
   python manage.py runserver
   ```
   Backend will be available at http://localhost:8000

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**
   ```bash
   npm install
   ```

3. **Start React development server**
   ```bash
   npm start
   ```
   Frontend will be available at http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Check the health indicator to ensure backend connection
3. Use the "Ask Question" tab to query the RAG system
4. Use the "Search Chunks" tab for debugging vector retrieval

## Development

### Backend Development

- API routes are in `api/routes/`
- Core logic in `rag/`, `embeddings/`, `vectorstore/`
- Configuration in `backend/settings.py`

### Frontend Development

- Main app in `frontend/src/App.js`
- Components in `frontend/src/components/`
- API calls use axios with proxy to backend

## Configuration

Key settings in `backend/settings.py`:

- `VECTOR_STORE_TYPE`: 'chroma' or 'faiss'
- `EMBEDDING_MODEL`: Sentence transformer model
- `LLM_MODEL`: OpenAI model via APIPE
- `CHUNK_SIZE`: Text chunk size for indexing
- `DEFAULT_TOP_K`: Default number of sources to retrieve

## Troubleshooting

- **CORS errors**: Ensure Django CORS settings allow frontend origin
- **Backend connection failed**: Check Django server is running on port 8000
- **No search results**: Ensure data is indexed in vector store
- **LLM errors**: Verify APIPE credentials and model availability

## License

[Add your license here]

# It loads your embedding ML model (local or remote) and exposes a simple embed() function.

import os, logging
from typing import List
logger = logging.getLogger(__name__)

USE_REMOTE = os.getenv("USE_REMOTE_EMBEDDING", "False") == "True"
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")
AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")

# Auto-enable remote embeddings if AIPIPE is configured and USE_REMOTE_EMBEDDING is not explicitly set
if not os.getenv("USE_REMOTE_EMBEDDING") and AIPIPE_BASE_URL and AIPIPE_API_KEY:
    USE_REMOTE = True

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")  # default local model

# Set embedding dimension based on model type
if USE_REMOTE:
    # Remote embeddings (OpenAI via AIPIPE) are typically 1536 dimensions
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
else:
    # Local SentenceTransformer models are typically 384 dimensions
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Local model (SentenceTransformers)
_local_model = None
def _init_local_model():
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            logger.error("sentence-transformers not installed: %s", e)
            raise
        _local_model = SentenceTransformer(EMBEDDING_MODEL)
    return _local_model

class EmbeddingClient:
    def __init__(self):
        self.use_remote = USE_REMOTE and AIPIPE_BASE_URL and AIPIPE_API_KEY
        if self.use_remote:
            import httpx
            self._http = httpx.Client(timeout=30)
            logger.info("EmbeddingClient: using remote AIPipe embeddings")
        else:
            _init_local_model()
            logger.info("EmbeddingClient: using local sentence-transformers model %s", EMBEDDING_MODEL)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.use_remote:
            return self._remote_embed(texts)
        return self._local_embed(texts)

    def _local_embed(self, texts: List[str]) -> List[List[float]]:
        model = _init_local_model()
        vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=False)
        # convert numpy arrays to lists if needed
        return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]

    def _remote_embed(self, texts: List[str]) -> List[List[float]]:
        # OpenAI-compatible embeddings API via AIPipe
        url = f"{AIPIPE_BASE_URL.rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {AIPIPE_API_KEY}"}
        payload = {"model": EMBEDDING_MODEL, "input": texts}
        resp = self._http.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        embeddings = [item["embedding"] for item in data.get("data", [])]
        return embeddings

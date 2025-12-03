from pydantic import BaseModel
from typing import Dict, List, Any

class ChunkEmbeddingModel(BaseModel):
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

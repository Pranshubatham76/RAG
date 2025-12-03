"""
Retrieval schema for vector database chunks.

This schema ensures every chunk inserted into vector DB is structured uniformly.
Also includes schema for retrieved chunks during query time.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChunkSchema(BaseModel):
    """
    Schema representing a chunk ready for vector DB insertion.
    
    Attributes:
        chunk_id: Unique identifier for the chunk (e.g., "post_12_chunk_0")
        text: The actual text content of the chunk
        embedding: Vector embedding of the text (List[float])
        meta: Metadata dictionary containing:
            - post_id: Discourse post ID
            - topic_id: Discourse topic ID
            - url: Full URL to the post
            - title: Topic title
            - timestamp: Creation timestamp
            - chunk_index: Index of chunk within the post
            - author: Optional author username
    """
    chunk_id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="Chunk text content")
    embedding: List[float] = Field(..., description="Embedding vector")
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata dictionary with post_id, topic_id, url, title, timestamp, chunk_index"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "post_12_chunk_0",
                "text": "This is paragraph one...",
                "embedding": [0.123, 0.532, 0.891, ...],
                "meta": {
                    "post_id": "12",
                    "topic_id": "5",
                    "url": "https://discourse.example.com/t/topic-slug/5/1",
                    "title": "Topic Title",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chunk_index": 0,
                    "author": "username"
                }
            }
        }


class RetrievedChunk(BaseModel):
    """
    Schema representing a chunk retrieved from vector DB during query time.
    
    Attributes:
        text: The chunk text content
        similarity: Similarity score (0.0 to 1.0)
        meta: Metadata dictionary containing:
            - post_id: Discourse post ID
            - topic_id: Discourse topic ID
            - url: Full URL to the post
            - title: Topic title
            - timestamp: Creation timestamp
            - chunk_index: Index of chunk within the post
            - author: Optional author username
        chunk_id: Optional chunk identifier
    """
    text: str = Field(..., description="Chunk text content")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata dictionary with post_id, topic_id, url, title, timestamp, chunk_index"
    )
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "The reading club is a community discussion forum...",
                "similarity": 0.85,
                "chunk_id": "post_12_chunk_0",
                "meta": {
                    "post_id": "12",
                    "topic_id": "5",
                    "url": "https://discourse.example.com/t/topic-slug/5/1",
                    "title": "Topic Title",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chunk_index": 0,
                    "author": "username"
                }
            }
        }


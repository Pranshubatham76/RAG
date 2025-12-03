"""
Ask Response Schema - Structures the final API response.

Purpose: Structure the final API response
Returns to: frontend UI
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Source(BaseModel):
    """Source citation from retrieved chunk."""
    url: str = Field(..., description="URL to the original post")
    title: str = Field(..., description="Topic title")
    post_id: Optional[str] = Field(None, description="Post ID")
    topic_id: Optional[str] = Field(None, description="Topic ID")
    similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Similarity score")
    chunk_text: Optional[str] = Field(None, description="Retrieved chunk text (preview)")


class AskResponse(BaseModel):
    """
    Response schema for the /ask endpoint.
    
    Attributes:
        answer: Generated answer from LLM
        sources: List of source citations
        latency_ms: Request processing time in milliseconds
        chunks_retrieved: Number of chunks used
        model_used: LLM model identifier (optional)
    """
    answer: str = Field(..., description="Generated answer from LLM")
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    latency_ms: float = Field(..., ge=0, description="Request latency in milliseconds")
    chunks_retrieved: int = Field(default=0, ge=0, description="Number of chunks retrieved")
    model_used: Optional[str] = Field(None, description="LLM model identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The reading club is a community discussion forum...",
                "sources": [
                    {
                        "url": "https://discourse.example.com/t/topic/123",
                        "title": "Reading Club Introduction",
                        "similarity": 0.85
                    }
                ],
                "latency_ms": 1532.5,
                "chunks_retrieved": 3,
                "model_used": "gpt-4"
            }
        }


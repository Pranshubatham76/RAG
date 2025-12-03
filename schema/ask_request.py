"""
Ask Request Schema - Validates incoming user query.

Purpose: Validate and structure the incoming user query
Input: JSON body from frontend
Returns to: query_engine.py
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class AskRequest(BaseModel):
    """
    Request schema for the /ask endpoint.
    
    Attributes:
        query: User's question/query string
        top_k: Number of similar chunks to retrieve (default: 5)
        max_tokens: Maximum tokens for LLM response (optional)
        temperature: LLM temperature (optional)
    """
    query: str = Field(..., min_length=1, max_length=1000, description="User's question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4000, description="Max tokens for response")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="LLM temperature")
    
    @validator('query')
    def query_not_empty(cls, v):
        """Ensure query is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the reading club about?",
                "top_k": 3
            }
        }


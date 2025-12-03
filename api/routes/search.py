"""
Search Route - Optional testing route for vector DB retrieval only.

Method: POST
Purpose: Debug vector DB retrieval without LLM
"""
import logging
import json
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from embeddings.embedder import embed_query
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def search(request):
    """
    Search endpoint: /api/v1/search
    
    Used for debugging vector DB retrieval only (no LLM).
    
    Request body:
        {
            "query": "search term",
            "top_k": 5
        }
    
    Response:
        {
            "query": "...",
            "results": [
                {
                    "text": "...",
                    "similarity": 0.85,
                    "meta": {...}
                }
            ],
            "count": 5
        }
    """
    try:
        # Parse request body
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400
            )
        
        query = body.get("query", "").strip()
        top_k = body.get("top_k", 5)
        
        if not query:
            return JsonResponse(
                {"error": "Query is required"},
                status=400
            )
        
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            top_k = 5
        
        logger.info(f"Search request: query='{query[:50]}...', top_k={top_k}")
        
        # Embed query
        query_embedding = embed_query(query)
        
        if not query_embedding:
            return JsonResponse(
                {"error": "Failed to generate query embedding"},
                status=500
            )
        
        # Retrieve chunks
        retriever = Retriever()
        retrieved_chunks = retriever.search(query_embedding, top_k=top_k)
        
        # Format results
        results = []
        for chunk in retrieved_chunks:
            results.append({
                "text": chunk.text,
                "similarity": chunk.similarity,
                "chunk_id": chunk.chunk_id,
                "meta": chunk.meta
            })
        
        response = {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
        logger.info(f"Search completed: {len(results)} results")
        
        return JsonResponse(response, status=200)
        
    except Exception as e:
        logger.exception(f"Error in /search endpoint: {e}")
        return JsonResponse(
            {
                "error": "Internal server error",
                "message": str(e)
            },
            status=500
        )


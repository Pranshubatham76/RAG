"""
Ask Route - Main RAG inference endpoint.

Method: POST
Body: AskRequest
Work: Runs complete query pipeline
"""
import logging
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from schema.ask_request import AskRequest
from schema.ask_response import AskResponse
from rag.query_engine import get_query_engine

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def ask(request):
    """
    Main RAG endpoint: /api/v1/ask
    
    Accepts a user query and returns an AI-generated answer with sources.
    
    Request body:
        {
            "query": "What is the reading club about?",
            "top_k": 3
        }
    
    Response:
        {
            "answer": "...",
            "sources": [...],
            "latency_ms": 1532.5,
            "chunks_retrieved": 3
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
        
        # Validate request
        try:
            ask_request = AskRequest(**body)
        except Exception as e:
            return JsonResponse(
                {"error": f"Invalid request: {str(e)}"},
                status=400
            )
        
        logger.info(f"Received query: {ask_request.query[:100]}...")
        
        # Get query engine and process
        query_engine = get_query_engine()
        response = query_engine.answer_question(ask_request)
        
        # Convert Pydantic model to dict for JSON response
        response_dict = response.dict()
        
        logger.info(
            f"Query answered: {len(response.answer)} chars, "
            f"{len(response.sources)} sources, {response.latency_ms:.0f}ms"
        )
        
        return JsonResponse(response_dict, status=200)
        
    except Exception as e:
        logger.exception(f"Error in /ask endpoint: {e}")
        return JsonResponse(
            {
                "error": "Internal server error",
                "message": str(e)
            },
            status=500
        )


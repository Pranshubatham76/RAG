"""
Health Route - Check if ingestion complete, DB working.

Method: GET
Purpose: Verify system state
"""
import logging
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from vectorstore.vector_store import get_vector_store
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health(request):
    """
    Health check endpoint: /api/v1/health
    
    Verifies:
    - Vector store is accessible
    - Data has been indexed
    - System is ready to answer queries
    
    Response:
        {
            "status": "healthy",
            "vector_store": {
                "type": "chroma",
                "count": 1200
            },
            "ready": true
        }
    """
    try:
        health_status = {
            "status": "healthy",
            "ready": False,
            "vector_store": {},
            "errors": []
        }
        
        # Check vector store
        try:
            store = get_vector_store()
            stats = store.get_stats()
            
            health_status["vector_store"] = {
                "type": stats.get("store_type", "unknown"),
                "count": stats.get("count", 0),
                "available": True
            }
            
            # Check if data is indexed
            count = stats.get("count", 0)
            if count > 0:
                health_status["ready"] = True
            else:
                health_status["errors"].append("No data indexed in vector store")
                health_status["status"] = "not_ready"
            
        except Exception as e:
            logger.exception("Vector store health check failed")
            health_status["vector_store"] = {
                "available": False,
                "error": str(e)
            }
            health_status["errors"].append(f"Vector store error: {str(e)}")
            health_status["status"] = "unhealthy"
        
        # Test retrieval (optional, can be slow)
        if health_status["ready"]:
            try:
                retriever = Retriever()
                # Quick test with dummy query
                test_embedding = [0.1] * 384  # Dummy vector
                test_results = retriever.search(test_embedding, top_k=1)
                health_status["retrieval_test"] = "passed" if test_results else "no_results"
            except Exception as e:
                logger.warning(f"Retrieval test failed: {e}")
                health_status["retrieval_test"] = "failed"
                health_status["errors"].append(f"Retrieval test error: {str(e)}")
        
        # Determine HTTP status
        http_status = 200
        if health_status["status"] == "unhealthy":
            http_status = 503
        elif health_status["status"] == "not_ready":
            http_status = 200  # Still 200, but ready=false
        
        logger.debug(f"Health check: status={health_status['status']}, ready={health_status['ready']}")
        
        return JsonResponse(health_status, status=http_status)
        
    except Exception as e:
        logger.exception(f"Error in /health endpoint: {e}")
        return JsonResponse(
            {
                "status": "error",
                "error": str(e),
                "ready": False
            },
            status=500
        )


"""
LLM Client - Send constructed prompt to AIPipe → OpenRouter → GPT model.

Purpose: Send constructed prompt to AIPipe → OpenRouter → GPT model
Input: Prompt dictionary/string
Output: Raw LLM answer
Returned to: query_engine.py
"""
import os
import logging
import time
from typing import Dict, Any, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")
AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))


class LLMClient:
    """
    Client for interacting with LLM via AIPipe/OpenRouter API.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            base_url: AIPipe base URL (default: from env)
            api_key: API key (default: from env)
            model: Model identifier (default: from env)
            timeout: Request timeout in seconds (default: from env)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for LLMClient. Install with: pip install httpx")
        
        self.base_url = (base_url or AIPIPE_BASE_URL or "").rstrip("/")
        self.api_key = api_key or AIPIPE_API_KEY
        self.model = model or LLM_MODEL
        self.timeout = timeout or LLM_TIMEOUT
        
        if not self.base_url:
            raise ValueError("AIPIPE_BASE_URL must be set")
        if not self.api_key:
            raise ValueError("AIPIPE_API_KEY must be set")
        
        self.client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"LLMClient initialized: model={self.model}, base_url={self.base_url[:50]}...")
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response from LLM.
        
        Args:
            prompt: Input prompt string
            max_tokens: Maximum tokens for response (default: from env)
            temperature: Sampling temperature (default: from env)
            **kwargs: Additional parameters for API
            
        Returns:
            Dictionary with:
                - answer: Generated text
                - model: Model used
                - usage: Token usage info (if available)
                - error: Error message (if failed)
        """
        max_tokens = max_tokens or LLM_MAX_TOKENS
        temperature = temperature if temperature is not None else LLM_TEMPERATURE
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            start_time = time.time()
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract answer from response
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No choices in LLM response")
            
            answer = choices[0].get("message", {}).get("content", "")
            
            if not answer:
                raise ValueError("Empty answer from LLM")
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            result = {
                "answer": answer.strip(),
                "model": data.get("model", self.model),
                "usage": data.get("usage", {}),
                "latency_ms": latency
            }
            
            logger.info(
                f"LLM generation successful: {len(answer)} chars, "
                f"{latency:.0f}ms, model={result['model']}"
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return {
                "answer": "",
                "error": error_msg,
                "model": self.model
            }
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.exception(error_msg)
            return {
                "answer": "",
                "error": error_msg,
                "model": self.model
            }
    
    def close(self):
        """Close HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance (optional)
_llm_client_instance = None

def get_llm_client(**kwargs) -> LLMClient:
    """
    Get or create LLM client singleton.
    
    Args:
        **kwargs: Arguments to pass to LLMClient constructor
        
    Returns:
        LLMClient instance
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient(**kwargs)
    return _llm_client_instance


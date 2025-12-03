"""
Query Engine - Main RAG Controller.

Purpose: Orchestrate the entire query pipeline
Flow: Parse user query → Embed query → Retrieve chunks → Build prompt → Generate answer → Return response
"""
import logging
import time
from typing import Dict, Any, Optional

from embeddings.embedder import embed_query
from rag.retriever import Retriever
from rag.prompt_builder import PromptBuilder
from rag.llm_client import LLMClient, get_llm_client
from schema.ask_request import AskRequest
from schema.ask_response import AskResponse, Source

logger = logging.getLogger(__name__)


class QueryEngine:
    """
    Main RAG query engine that orchestrates the entire query pipeline.
    
    This class coordinates:
    1. Query embedding
    2. Vector retrieval
    3. Prompt construction
    4. LLM generation
    5. Response formatting
    """
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize query engine.
        
        Args:
            retriever: Retriever instance (default: creates new)
            prompt_builder: PromptBuilder instance (default: creates new)
            llm_client: LLMClient instance (default: creates new)
        """
        self.retriever = retriever or Retriever()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.llm_client = llm_client
        
        logger.info("QueryEngine initialized")
    
    def answer_question(
        self,
        request: AskRequest,
        llm_client: Optional[LLMClient] = None
    ) -> AskResponse:
        """
        Answer a user question using RAG pipeline.
        
        This is the main method that runs the complete query pipeline:
        1. Embed user query
        2. Retrieve similar chunks
        3. Build RAG prompt
        4. Generate answer via LLM
        5. Format response
        
        Args:
            request: AskRequest with user query and parameters
            llm_client: Optional LLM client (uses instance default if not provided)
            
        Returns:
            AskResponse with answer, sources, and metadata
        """
        start_time = time.time()
        
        # Use provided client or instance client or get default
        client = llm_client or self.llm_client
        if not client:
            try:
                client = get_llm_client()
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                return AskResponse(
                    answer="Sorry, I'm unable to generate answers at the moment. Please try again later.",
                    sources=[],
                    latency_ms=(time.time() - start_time) * 1000,
                    chunks_retrieved=0
                )
        
        try:
            # Step 1: Embed user query
            logger.info(f"Embedding query: {request.query[:50]}...")
            query_embedding = embed_query(request.query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return AskResponse(
                    answer="Sorry, I encountered an error processing your query.",
                    sources=[],
                    latency_ms=(time.time() - start_time) * 1000,
                    chunks_retrieved=0
                )
            
            # Step 2: Retrieve similar chunks
            logger.info(f"Retrieving top {request.top_k} chunks...")
            retrieved_chunks = self.retriever.search(
                query_embedding,
                top_k=request.top_k
            )
            
            if not retrieved_chunks:
                logger.warning("No chunks retrieved from vector store")
                return AskResponse(
                    answer="I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your question or check if the data has been indexed.",
                    sources=[],
                    latency_ms=(time.time() - start_time) * 1000,
                    chunks_retrieved=0
                )
            
            # Step 3: Build RAG prompt
            logger.info(f"Building prompt with {len(retrieved_chunks)} chunks...")
            prompt = self.prompt_builder.create_prompt(
                user_query=request.query,
                retrieved_chunks=retrieved_chunks
            )
            
            # Step 4: Generate answer via LLM
            logger.info("Generating answer via LLM...")
            llm_result = client.generate(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            if llm_result.get("error"):
                logger.error(f"LLM error: {llm_result['error']}")
                return AskResponse(
                    answer=f"Sorry, I encountered an error: {llm_result['error']}",
                    sources=[],
                    latency_ms=(time.time() - start_time) * 1000,
                    chunks_retrieved=len(retrieved_chunks)
                )
            
            answer = llm_result.get("answer", "")
            if not answer:
                answer = "I couldn't generate a response. Please try again."
            
            # Step 5: Format sources
            sources = []
            for chunk in retrieved_chunks:
                meta = chunk.meta or {}
                source = Source(
                    url=meta.get("url", ""),
                    title=meta.get("title", "Untitled"),
                    post_id=meta.get("post_id"),
                    topic_id=meta.get("topic_id"),
                    similarity=chunk.similarity,
                    chunk_text=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                )
                sources.append(source)
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            
            # Build response
            response = AskResponse(
                answer=answer,
                sources=sources,
                latency_ms=total_latency,
                chunks_retrieved=len(retrieved_chunks),
                model_used=llm_result.get("model")
            )
            
            logger.info(
                f"Query answered successfully: {len(answer)} chars, "
                f"{len(sources)} sources, {total_latency:.0f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.exception(f"Error in query pipeline: {e}")
            return AskResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                latency_ms=(time.time() - start_time) * 1000,
                chunks_retrieved=0
            )


# Singleton instance (optional)
_query_engine_instance = None

def get_query_engine(**kwargs) -> QueryEngine:
    """
    Get or create query engine singleton.
    
    Args:
        **kwargs: Arguments to pass to QueryEngine constructor
        
    Returns:
        QueryEngine instance
    """
    global _query_engine_instance
    if _query_engine_instance is None:
        _query_engine_instance = QueryEngine(**kwargs)
    return _query_engine_instance


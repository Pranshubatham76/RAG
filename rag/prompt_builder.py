"""
Prompt Builder - Merge user question, retrieved chunks, and system instructions.

Purpose: Merge user question, retrieved chunks, and system instructions into final prompt
Output: Fully formatted prompt string
Returned to: llm_client.py
"""
import logging
from typing import List, Optional

from schema.retrieval_schema import RetrievedChunk

logger = logging.getLogger(__name__)

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context from a Discourse forum discussion.

Your task is to:
1. Answer the user's question using ONLY the information provided in the context
2. If the context doesn't contain enough information, say so clearly
3. Cite specific sources when referencing information
4. Be concise but comprehensive
5. If asked about something not in the context, politely indicate you don't have that information

Context will be provided as numbered chunks from Discourse posts."""


class PromptBuilder:
    """
    Builds RAG prompts by combining user query, retrieved chunks, and system instructions.
    """
    
    def __init__(self, system_prompt: Optional[str] = None, max_context_length: int = 3000):
        """
        Initialize prompt builder.
        
        Args:
            system_prompt: Custom system prompt (default: uses DEFAULT_SYSTEM_PROMPT)
            max_context_length: Maximum characters for context (to avoid token limits)
        """
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_context_length = max_context_length
        logger.debug("PromptBuilder initialized")
    
    def create_prompt(
        self,
        user_query: str,
        retrieved_chunks: List[RetrievedChunk],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Create a RAG prompt from user query and retrieved chunks.
        
        Args:
            user_query: User's question
            retrieved_chunks: List of retrieved chunks with context
            system_prompt: Override system prompt (optional)
            
        Returns:
            Fully formatted prompt string
        """
        system = system_prompt or self.system_prompt
        
        # Build context section from retrieved chunks
        context_parts = []
        total_length = 0
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            chunk_text = chunk.text.strip()
            if not chunk_text:
                continue
            
            # Format chunk with metadata
            chunk_entry = f"[{i}] {chunk_text}"
            
            # Add metadata if available
            meta = chunk.meta or {}
            if meta.get("title"):
                chunk_entry += f"\n   (Source: {meta.get('title')})"
            
            # Check length limit
            if total_length + len(chunk_entry) > self.max_context_length:
                logger.warning(
                    f"Context length limit reached ({self.max_context_length} chars), "
                    f"truncating at chunk {i}"
                )
                break
            
            context_parts.append(chunk_entry)
            total_length += len(chunk_entry)
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant context found."
        
        # Build final prompt
        prompt = f"""{system}

Context from Discourse forum:
{context}

User Question: {user_query}

Please provide a helpful answer based on the context above. If the context doesn't contain enough information to answer the question, please say so."""
        
        logger.debug(f"Created prompt with {len(context_parts)} chunks, {len(prompt)} characters")
        return prompt
    
    def create_simple_prompt(
        self,
        user_query: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> str:
        """
        Create a simpler prompt format (alternative to full RAG prompt).
        
        Args:
            user_query: User's question
            retrieved_chunks: List of retrieved chunks
            
        Returns:
            Simplified prompt string
        """
        context = "\n\n".join([
            f"Chunk {i+1}: {chunk.text[:500]}..."
            for i, chunk in enumerate(retrieved_chunks[:5])
        ])
        
        return f"""Based on the following context, answer the question.

Context:
{context}

Question: {user_query}

Answer:"""


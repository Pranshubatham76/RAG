"""
Text Chunker - Split text into overlapping chunks.

Purpose: Split long text into smaller overlapping chunks (200-500 tokens)
Input: A single cleaned text string
Output: List of chunk dictionaries with text and chunk_index
Returns to: embedder.py
"""
from typing import List, Dict, Any
import os
import uuid
import logging

import re

try:
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))  # Approximate words per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # Overlap in words


def _simple_sentence_tokenize(text: str) -> List[str]:
    """
    Fallback sentence tokenizer if NLTK is not available.
    Uses regex to split on sentence boundaries.
    """
    # Split on sentence endings (. ! ?) followed by space or newline
    sentences = re.split(r'([.!?]+\s+)', text)
    # Recombine sentences with their punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            result.append(sentences[i] + sentences[i + 1])
        else:
            result.append(sentences[i])
    # Filter empty sentences
    return [s.strip() for s in result if s.strip()]


def split_into_chunks(
    text: str,
    chunk_size: int = None,
    overlap: int = None
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks.
    
    Strategy:
    1. Split text into sentences
    2. Group sentences into chunks of approximately chunk_size words
    3. Create overlap by including last N words from previous chunk
    
    Args:
        text: Input text to chunk
        chunk_size: Target words per chunk (defaults to CHUNK_SIZE env var)
        overlap: Overlap in words between chunks (defaults to CHUNK_OVERLAP env var)
        
    Returns:
        List of chunk dictionaries:
        [
            {
                "chunk_id": "uuid",
                "chunk_index": 0,
                "text": "chunk text...",
                "meta": {}
            },
            ...
        ]
    """
    if not text or not text.strip():
        return []
    
    chunk_size = chunk_size or CHUNK_SIZE
    overlap = overlap or CHUNK_OVERLAP
    
    # Ensure overlap is less than chunk_size
    overlap = min(overlap, chunk_size - 1)
    
    # Tokenize into sentences
    if NLTK_AVAILABLE:
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sent_tokenize failed: {e}, using fallback")
            sentences = _simple_sentence_tokenize(text)
    else:
        sentences = _simple_sentence_tokenize(text)
    
    if not sentences:
        return []
    
    chunks = []
    current_chunk_sentences = []
    current_word_count = 0
    chunk_index = 0
    
    def create_chunk(sentences_list: List[str], idx: int) -> Dict[str, Any]:
        """Helper to create a chunk dictionary from sentences."""
        if not sentences_list:
            return None
        
        chunk_text = " ".join(sentences_list)
        return {
            "chunk_id": str(uuid.uuid4()),
            "chunk_index": idx,
            "text": chunk_text.strip(),
            "meta": {}
        }
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_word_count = len(sentence.split())
        
        # Handle case where a single sentence is longer than chunk_size
        if sentence_word_count >= chunk_size:
            # Flush current chunk if it has content
            if current_chunk_sentences:
                chunk = create_chunk(current_chunk_sentences, chunk_index)
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1
                current_chunk_sentences = []
                current_word_count = 0
            
            # Split the long sentence by words
            words = sentence.split()
            word_idx = 0
            while word_idx < len(words):
                # Take chunk_size words
                chunk_words = words[word_idx:word_idx + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "meta": {}
                })
                chunk_index += 1
                
                # Move forward by (chunk_size - overlap) for overlap
                word_idx += chunk_size - overlap
                if word_idx >= len(words):
                    break
            
            i += 1
            continue
        
        # Check if adding this sentence would exceed chunk_size
        if current_word_count + sentence_word_count <= chunk_size:
            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_word_count += sentence_word_count
            i += 1
        else:
            # Flush current chunk
            if current_chunk_sentences:
                chunk = create_chunk(current_chunk_sentences, chunk_index)
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1
            
            # Start new chunk with overlap
            if overlap > 0 and current_chunk_sentences:
                # Take last N words from previous chunk for overlap
                overlap_words = []
                for sent in reversed(current_chunk_sentences):
                    words_in_sent = sent.split()
                    remaining_overlap = overlap - len(overlap_words)
                    if remaining_overlap <= 0:
                        break
                    
                    # Take words from end of sentence
                    take_count = min(len(words_in_sent), remaining_overlap)
                    overlap_words = words_in_sent[-take_count:] + overlap_words
                
                if overlap_words:
                    current_chunk_sentences = [" ".join(overlap_words)]
                    current_word_count = len(overlap_words)
                else:
                    current_chunk_sentences = []
                    current_word_count = 0
            else:
                current_chunk_sentences = []
                current_word_count = 0
    
    # Flush remaining chunk
    if current_chunk_sentences:
        chunk = create_chunk(current_chunk_sentences, chunk_index)
        if chunk:
            chunks.append(chunk)
    
    logger.debug(f"Created {len(chunks)} chunks from text of {len(text)} characters")
    return chunks


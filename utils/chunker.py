# backend/app/utils/chunker.py
from typing import List, Dict, Any
import os, math, uuid
from nltk.tokenize import sent_tokenize



CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))  # approx words
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    sentences = sent_tokenize(text)
    words = [s.split() for s in sentences]
    chunks = []
    current = []
    current_word_count = 0
    idx = 0
    chunk_index = 0

    def flush_chunk(cur_sentences, index):
        if not cur_sentences:
            return None
        chunk_text = " ".join(cur_sentences)
        return {
            "chunk_id": str(uuid.uuid4()),
            "chunk_index": index,
            "text": chunk_text,
            "meta": {}
        }

    i = 0
    while i < len(sentences):
        s = sentences[i]
        count = len(s.split())
        # if single sentence longer than chunk_size, split by words
        if count >= chunk_size:
            # flush current
            if current:
                c = flush_chunk(current, chunk_index)
                if c: chunks.append(c); chunk_index += 1
                current, current_word_count = [], 0
            # split the sentence into word-based chunks
            words_in_sentence = s.split()
            w_i = 0
            while w_i < len(words_in_sentence):
                part = " ".join(words_in_sentence[w_i:w_i+chunk_size])
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_index": chunk_index,
                    "text": part,
                    "meta": {}
                })
                chunk_index += 1
                w_i += chunk_size - overlap
            i += 1
            continue

        if current_word_count + count <= chunk_size:
            current.append(s)
            current_word_count += count
            i += 1
        else:
            c = flush_chunk(current, chunk_index)
            if c:
                chunks.append(c)
                chunk_index += 1
            # start new chunk with overlap from previous chunk's end
            if overlap > 0:
                # we create overlap by taking last `overlap` words from current (if exist)
                last_words = []
                for sent in reversed(current):
                    ws = sent.split()
                    if not ws: continue
                    take = min(len(ws), overlap - len(last_words))
                    last_words = ws[-take:] + last_words
                    if len(last_words) >= overlap:
                        break
                if last_words:
                    current = [" ".join(last_words)]
                    current_word_count = len(last_words)
                else:
                    current = []
                    current_word_count = 0
            else:
                current = []
                current_word_count = 0
    # flush remaining
    if current:
        c = flush_chunk(current, chunk_index)
        if c:
            chunks.append(c)
    return chunks

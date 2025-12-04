# backend/app/vectorstore/chroma_store.py
"""
Chroma-backed vector store implementation.

Requirements:
    pip install chromadb

Uses duckdb+parquet persistence by default (persist_directory).
This module intentionally validates inputs and returns consistent results
compatible with a FAISS fallback implementation.
"""
from __future__ import annotations
import os
import logging
from typing import List, Dict, Any, Sequence, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vectorstore")
DEFAULT_COLLECTION = os.getenv("VECTOR_STORE_COLLECTION", "discourse_posts")
_CHROMA_DB_IMPL = os.getenv("CHROMA_DB_IMPL", "duckdb+parquet")  # recommended for local persistence

class ChromaStore:
    def __init__(self, persist_directory: Optional[str] = None, collection_name: Optional[str] = None):
        """
        Initialize Chroma client and collection. Raises ImportError if chromadb isn't installed.
        """
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except Exception as e:
            logger.exception("chromadb is not installed or cannot be imported: %s", e)
            raise ImportError("chromadb is required for ChromaStore but is not available") from e

        persist_directory = persist_directory or DEFAULT_STORE_PATH
        collection_name = collection_name or DEFAULT_COLLECTION
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # create client with persistence
        try:
            # Try ChromaDB 1.0+ API (without tenant/database for local persistence)
            try:
                self._client = chromadb.PersistentClient(
                    path=persist_directory,
                    # Don't specify tenant/database for local persistence
                )
                logger.debug("Using ChromaDB PersistentClient (v1.0+ API)")
            except (ValueError, AttributeError) as e:
                # If tenant error, try without tenant validation
                logger.warning(f"ChromaDB tenant error, trying alternative initialization: {e}")
                # Try with explicit settings to bypass tenant validation
                try:
                    from chromadb.config import Settings
                    settings = Settings(
                        chroma_db_impl=_CHROMA_DB_IMPL,
                        persist_directory=persist_directory,
                        anonymized_telemetry=False
                    )
                    self._client = chromadb.Client(settings)
                    logger.debug("Using ChromaDB Client (with Settings)")
                except Exception as e3:
                    # Last resort: try old API
                    logger.warning("Trying old ChromaDB API")
                    settings = ChromaSettings(chroma_db_impl=_CHROMA_DB_IMPL, persist_directory=persist_directory)
                    self._client = chromadb.Client(settings)
                    logger.debug("Using ChromaDB Client (old API)")
        except Exception as e:
            logger.exception("Failed to initialize ChromaDB")
            raise RuntimeError(f"Could not initialize ChromaDB: {e}") from e
        # get or create collection
        try:
            self._collection = self._client.get_collection(collection_name)
        except Exception:
            self._collection = self._client.create_collection(collection_name)

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        logger.info("ChromaStore initialized: collection=%s persist_directory=%s", collection_name, persist_directory)

    def _validate_docs(self, docs: List[Dict[str, Any]]):
        if not isinstance(docs, list):
            raise ValueError("docs must be a list of dicts")
        for d in docs:
            if "chunk_id" not in d:
                raise ValueError("each doc must contain 'chunk_id'")
            if "embedding" not in d:
                raise ValueError("each doc must contain 'embedding'")

    def add_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add new documents to collection. Expects docs list with keys:
          - chunk_id (str)
          - text/document (optional)
          - embedding (Sequence[float])
          - meta (dict) optional
        """
        self._validate_docs(docs)
        ids = [d["chunk_id"] for d in docs]
        documents = [d.get("text", "") for d in docs]
        metadatas = [d.get("meta", {}) for d in docs]
        embeddings = [list(d["embedding"]) for d in docs]

        try:
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            # attempt persist (no-op if client does it automatically)
            try:
                self._client.persist()
            except Exception:
                # not fatal
                pass
            return {"status": "ok", "inserted": len(ids)}
        except Exception as e:
            logger.exception("Chroma add_documents failed: %s", e)
            raise

    def upsert_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upsert semantics: if id exists, update; else insert.
        Chroma client does not have a single upsert method in all versions;
        using add (which may error on existing ids) + delete+add fallback.
        """
        self._validate_docs(docs)
        ids = [d["chunk_id"] for d in docs]
        try:
            # try simple add; if it fails due to duplicates, fallback to delete+add
            return self.add_documents(docs)
        except Exception:
            logger.warning("Chroma add failed; attempting delete+add for upsert")
            try:
                self.delete(ids)
            except Exception:
                logger.exception("delete during upsert failed; continuing with add")
            return self.add_documents(docs)

    def search(self, query_vector: Sequence[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query by embedding. Returns list of hits:
        [
            {"chunk_id": id, "score": similarity_score (0..1), "text": doc, "meta": metadata}
        ]
        Note: chroma returns 'distances' which depending on config may be similarity or distance.
        We map distances -> (1 - dist) assuming distances in [0,1]; if larger, user should interpret.
        """
        if not hasattr(self, "_collection"):
            raise RuntimeError("Chroma collection not initialized")
        try:
            results = self._collection.query(query_embeddings=[list(query_vector)], n_results=top_k)
            ids = results.get("ids", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            documents = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            hits = []
            for cid, meta, doc, dist in zip(ids, metadatas, documents, distances):
                # convert distance to pseudo-similarity for UI; clamp to [0,1]
                score = 1.0 - float(dist) if isinstance(dist, (float, int)) else 0.0
                if score < 0:
                    # scale if distances are large; fallback to 0..1 normalization (best-effort)
                    try:
                        score = 1.0 / (1.0 + float(dist))
                    except Exception:
                        score = 0.0
                hits.append({"chunk_id": cid, "score": float(score), "text": doc, "meta": meta})
            return hits
        except Exception as e:
            logger.exception("Chroma search failed: %s", e)
            raise

    def delete(self, ids: List[str]) -> Dict[str, Any]:
        """
        Delete by ids (chunk_id)
        """
        try:
            self._collection.delete(ids=ids)
            try:
                self._client.persist()
            except Exception:
                pass
            return {"status": "ok", "deleted": len(ids)}
        except Exception as e:
            logger.exception("Chroma delete failed: %s", e)
            raise

    def clear(self) -> None:
        """
        Clear the entire collection (remove and recreate).
        """
        try:
            # chroma client supports delete_collection in many releases; some need client deletion
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                # fallback: delete individual ids if deletion is unsupported
                try:
                    ids = [r[0] for r in self._collection.get(include=["ids"]).get("ids", [[]])[0]]
                    if ids:
                        self._collection.delete(ids=ids)
                except Exception:
                    pass
            # recreate collection
            try:
                self._collection = self._client.create_collection(self.collection_name)
            except Exception:
                # if create_collection fails (e.g., collection existed), just pass
                pass
        except Exception as e:
            logger.exception("Chroma clear failed: %s", e)
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Return basic stats: count, dimension (if known), path info.
        """
        stats = {"store_type": "chroma", "collection": self.collection_name, "persist_directory": self.persist_directory}
        try:
            # chroma collection may expose count through .count() or .get
            try:
                # Get all documents to count (with minimal data)
                info = self._collection.get(include=["metadatas"])
                ids_list = info.get("ids", [])
                if ids_list:
                    # ids can be a list or list of lists depending on chroma version
                    if ids_list and isinstance(ids_list[0], list):
                        stats["count"] = len(ids_list[0])
                    else:
                        stats["count"] = len(ids_list)
                else:
                    stats["count"] = 0
            except Exception as e:
                # Fallback: try count() method if available
                try:
                    stats["count"] = self._collection.count()
                except Exception:
                    stats["count"] = 0
        except Exception:
            stats["count"] = 0
        return stats

    def persist(self) -> None:
        try:
            self._client.persist()
        except Exception:
            logger.exception("Chroma persist failed (non-fatal)")

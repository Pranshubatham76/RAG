# backend/app/vectorstore/faiss_store.py
"""
FAISS-backed vector store implementation with JSON metadata persistence.

Requirements:
    pip install faiss-cpu numpy

This implementation keeps a FAISS IndexFlatL2 in memory and persists:
    - the FAISS index file at <store_path>/faiss_index.index
    - metadata mapping file at <store_path>/faiss_meta.json

Docs format expected:
    {
        "chunk_id": str,
        "text": str,
        "embedding": Sequence[float],
        "meta": dict
    }
"""
from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Any, Sequence, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vectorstore")
META_FILENAME = "faiss_meta.json"
INDEX_FILENAME = "faiss_index.index"

class FaissStore:
    def __init__(self, store_path: Optional[str] = None):
        try:
            import faiss
            import numpy as np
        except Exception as e:
            logger.exception("faiss or numpy not available: %s", e)
            raise ImportError("faiss and numpy are required for FaissStore") from e

        self.faiss = faiss
        self.np = np
        self.store_path = Path(store_path or DEFAULT_STORE_PATH)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.store_path / META_FILENAME
        self.index_path = self.store_path / INDEX_FILENAME

        self.index = None  # faiss.Index
        self.dim = None
        # meta mapping: idx (int) -> {"chunk_id":..., "meta":..., "text":...}
        self.meta: Dict[str, Dict[str, Any]] = {}
        self._load_index_and_meta()
        logger.info("FaissStore initialized at %s", str(self.store_path))

    def _load_index_and_meta(self):
        # load meta if available
        if self.meta_path.exists():
            try:
                with self.meta_path.open("r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception:
                logger.exception("Failed to load faiss meta file; starting fresh")
                self.meta = {}
        else:
            self.meta = {}

        # load index if available
        if self.index_path.exists():
            try:
                self.index = self.faiss.read_index(str(self.index_path))
                # derive dim if possible
                self.dim = self.index.d
            except Exception:
                logger.exception("Failed to load faiss index; starting fresh")
                self.index = None

    def _save_index_and_meta(self):
        if self.index is not None:
            try:
                self.faiss.write_index(self.index, str(self.index_path))
            except Exception:
                logger.exception("Failed to write faiss index")
        try:
            with self.meta_path.open("w", encoding="utf-8") as f:
                json.dump(self.meta, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Failed to write faiss meta file")

    def _validate_docs(self, docs: List[Dict[str, Any]]):
        if not isinstance(docs, list):
            raise ValueError("docs must be a list")
        for d in docs:
            if "chunk_id" not in d or "embedding" not in d:
                raise ValueError("each doc must have 'chunk_id' and 'embedding'")

    def add_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Append vectors to the FAISS index. chunk_id -> new internal numeric id.
        """
        self._validate_docs(docs)
        # prepare array
        vecs = self.np.array([list(d["embedding"]) for d in docs], dtype="float32")
        n, dim = vecs.shape
        if self.index is None:
            # create flat L2 index
            self.index = self.faiss.IndexFlatL2(dim)
            self.dim = dim
        elif dim != self.dim:
            raise ValueError(f"Dimension mismatch: index dim {self.dim}, docs dim {dim}")

        start_idx = len(self.meta)
        self.index.add(vecs)
        # update meta mapping for new indices
        for i, d in enumerate(docs):
            idx = start_idx + i
            self.meta[str(idx)] = {"chunk_id": d["chunk_id"], "meta": d.get("meta", {}), "text": d.get("text", "")}
        self._save_index_and_meta()
        return {"status": "ok", "inserted": n}

    def upsert_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upsert in FAISS requires rebuilding index (FAISS flat index does not support in-place deletion easily).
        Strategy:
          - if chunk_ids are new, append
          - if chunk_ids already exist, rebuild index with replaced vectors
        For production you might use an index that supports removals (IVF + id map), but for simplicity
        we will rebuild when we encounter existing ids.
        """
        self._validate_docs(docs)
        # map existing chunk_id -> idx in meta
        existing_map = {v["chunk_id"]: int(k) for k, v in self.meta.items()}
        new_docs = []
        replace_map = {}
        for d in docs:
            cid = d["chunk_id"]
            if cid in existing_map:
                replace_map[existing_map[cid]] = d
            else:
                new_docs.append(d)
        # if we need to replace some vectors, rebuild index entirely
        if replace_map:
            # reconstruct full list of vectors in order of meta keys
            all_items = []
            # meta keys are numeric strings '0','1',...
            # build list of vectors by reading existing metadata and replacing where needed
            total = len(self.meta)
            for i in range(total):
                key = str(i)
                if i in replace_map:
                    all_items.append(replace_map[i])
                else:
                    rec = self.meta[key]
                    all_items.append({"chunk_id": rec["chunk_id"], "text": rec.get("text", ""), "embedding": None, "meta": rec.get("meta", {})})
            # fill embedding for those without embedding by attempting to find them in docs (otherwise fail)
            # we will load embeddings for existing ones from docs list if provided; otherwise raise
            # Build new vector list
            vectors = []
            for rec in all_items:
                if rec.get("embedding") is not None:
                    vectors.append(list(rec["embedding"]))
                else:
                    # find in docs (should be present in replace_map)
                    found = next((x for x in docs if x["chunk_id"] == rec["chunk_id"]), None)
                    if found and "embedding" in found:
                        vectors.append(list(found["embedding"]))
                    else:
                        raise ValueError("Cannot rebuild index: missing embedding for existing chunk_id " + rec["chunk_id"])
            # rebuild index
            vecs_np = self.np.array(vectors, dtype="float32")
            self.index = self.faiss.IndexFlatL2(vecs_np.shape[1])
            self.index.add(vecs_np)
            # rebuild meta mapping
            new_meta = {}
            for i, rec in enumerate(all_items):
                new_meta[str(i)] = {"chunk_id": rec["chunk_id"], "meta": rec.get("meta", {}), "text": rec.get("text", "")}
            self.meta = new_meta
            # append new docs
            if new_docs:
                vecs_new = self.np.array([list(d["embedding"]) for d in new_docs], dtype="float32")
                self.index.add(vecs_new)
                start = len(self.meta)
                for i, d in enumerate(new_docs):
                    self.meta[str(start + i)] = {"chunk_id": d["chunk_id"], "meta": d.get("meta", {}), "text": d.get("text", "")}
            self._save_index_and_meta()
            return {"status": "ok", "upserted": len(docs)}
        else:
            # just append new docs
            return self.add_documents(new_docs)

    def search(self, query_vector: Sequence[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None:
            return []
        q = self.np.array([list(query_vector)], dtype="float32")
        D, I = self.index.search(q, top_k)
        hits = []
        for dist, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            rec = self.meta.get(str(int(idx)), {})
            # convert L2 distance to a heuristic similarity
            score = 1.0 / (1.0 + float(dist)) if float(dist) >= 0 else 0.0
            hits.append({"chunk_id": rec.get("chunk_id"), "score": float(score), "text": rec.get("text"), "meta": rec.get("meta")})
        return hits

    def delete(self, ids: List[str]) -> Dict[str, Any]:
        """
        Delete requires rebuilding index excluding the removed ids.
        For small collections this is fine; for very large collections consider more advanced FAISS indices.
        """
        # build new list excluding ids
        kept = []
        for idx_str, rec in list(self.meta.items()):
            if rec.get("chunk_id") in ids:
                continue
            kept.append(rec)
        # need embeddings for kept items to rebuild index
        if not kept:
            # delete all
            self.index = None
            self.meta = {}
            # remove persisted files
            try:
                if self.index_path.exists():
                    self.index_path.unlink()
                if self.meta_path.exists():
                    self.meta_path.unlink()
            except Exception:
                pass
            return {"status": "ok", "deleted": len(ids)}
        # rebuild index with kept items
        vectors = []
        for rec in kept:
            # we stored original text, but not embeddings. to rebuild we require embeddings input.
            # We expect consumer to provide full replacement docs or we cannot rebuild.
            # For safety, we will error here to force the caller to reindex or provide up-to-date embeddings.
            raise NotImplementedError("FAISS delete for partial sets requires re-indexing from source or storing embeddings separately.")
        # unreachable
        return {"status": "ok", "deleted": 0}

    def clear(self) -> None:
        try:
            if self.index_path.exists():
                self.index_path.unlink()
            if self.meta_path.exists():
                self.meta_path.unlink()
        except Exception:
            logger.exception("Failed to remove persisted faiss files")
        self.index = None
        self.meta = {}
        self.dim = None

    def get_stats(self) -> Dict[str, Any]:
        return {"store_type": "faiss", "store_path": str(self.store_path), "count": len(self.meta), "dim": self.dim}

    def persist(self) -> None:
        self._save_index_and_meta()

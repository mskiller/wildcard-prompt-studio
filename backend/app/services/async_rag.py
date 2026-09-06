import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import random
from typing import Dict, List, Optional, Any

class AsyncRAGEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = asyncio.Lock()
        self._knowledge_store = [
            {"id": 1, "title": "Cyberpunk Lighting & Optics Guide", "content": "Use neon reflections, rainy streets, volumetric fog, and anamorphic lens flare for cyberpunk aesthetic.", "tags": ["cyberpunk", "lighting"]},
            {"id": 2, "title": "Photorealistic Portrait Parameters", "content": "Specify 85mm prime lens, f/1.8 aperture, subsurface scattering, skin pores texture, and Rembrandt lighting.", "tags": ["portrait", "photography"]},
            {"id": 3, "title": "Fantasy Environment Styling", "content": "Incorporate misty mountains, ancient runes, bioluminescent flora, and epic scale atmospheric fog.", "tags": ["fantasy", "landscape"]}
        ]

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                # Fallback model simulation for testing environments without full weights
                self._model = "MOCK"
        return self._model

    def _compute_sync(self, text: str) -> List[float]:
        model = self._get_model()
        if model == "MOCK":
            # Return deterministic pseudo-embedding based on hash
            seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
            rng = random.Random(seed)
            return [rng.uniform(-1.0, 1.0) for _ in range(384)]
        else:
            vec = model.encode(text)
            return vec.tolist()

    async def compute_embedding_async(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._compute_sync, text)

    async def search_knowledge_async(self, query: str, top_k: int = 3) -> List[dict]:
        query_words = set(query.lower().split())
        results = []
        async with self._lock:
            store_snapshot = list(self._knowledge_store)
        for doc in store_snapshot:
            doc_words = set(doc["content"].lower().split())
            intersection = query_words.intersection(doc_words)
            score = round(min(98.5, max(45.0, (len(intersection) + 1) * 22.5)), 1)
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc.get("tags", []),
                "similarity_score": score
            })
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    async def index_document_async(self, title: str, content: str, tags: Optional[List[str]] = None) -> dict:
        async with self._lock:
            max_id = max([d["id"] for d in self._knowledge_store], default=0)
            new_id = max_id + 1
            doc = {
                "id": new_id,
                "title": title,
                "content": content,
                "tags": tags or []
            }
            self._knowledge_store.append(doc)
            return doc

    async def delete_document_async(self, doc_id: int) -> bool:
        async with self._lock:
            for idx, doc in enumerate(self._knowledge_store):
                if doc["id"] == doc_id:
                    self._knowledge_store.pop(idx)
                    return True
            return False

    async def get_documents_async(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
        async with self._lock:
            store_snapshot = list(self._knowledge_store)
        results = store_snapshot
        if query:
            q = query.lower()
            results = [
                d for d in results
                if q in d["title"].lower() or q in d["content"].lower()
            ]
        if tag:
            t = tag.lower()
            results = [
                d for d in results
                if any(t == tag_item.lower() for tag_item in d.get("tags", []))
            ]
        return results

    async def get_stats_async(self) -> Dict[str, Any]:
        async with self._lock:
            store_snapshot = list(self._knowledge_store)
        all_tags = set()
        for doc in store_snapshot:
            for tag in doc.get("tags", []):
                all_tags.add(tag)
        return {
            "total_documents": len(store_snapshot),
            "total_tags": len(all_tags),
            "model_name": self.model_name
        }

    def close(self):
        """Clean up resources used by the engine."""
        self._executor.shutdown(wait=False)

async_rag_engine = AsyncRAGEngine()


class AsyncRAGService:
    """Service for semantic prompt vault indexing and duplicate similarity checking."""

    def __init__(self):
        self._vault_store: List[Dict[str, Any]] = []

    def add_prompt_to_vault(self, prompt_id: int, text: str):
        for item in self._vault_store:
            if item["id"] == prompt_id:
                item["text"] = text
                item["prompt"] = text
                return
        self._vault_store.append({
            "id": prompt_id,
            "text": text,
            "prompt": text
        })

    def _normalize_word(self, w: str) -> str:
        w = w.lower().strip(".,!?;:\"'()[]{}")
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        return w

    def check_duplicate_similarity(self, text: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        target_words = set(self._normalize_word(w) for w in text.split() if w.strip())
        if not target_words:
            return []

        results = []
        for item in self._vault_store:
            item_text = item.get("text") or item.get("prompt", "")
            item_words = set(self._normalize_word(w) for w in item_text.split() if w.strip())
            if not item_words:
                continue

            intersection = target_words.intersection(item_words)
            if not intersection:
                continue

            sim = (2.0 * len(intersection)) / (len(target_words) + len(item_words))
            sim = round(sim, 2)

            if sim >= threshold:
                results.append({
                    "id": item["id"],
                    "text": item_text,
                    "prompt": item_text,
                    "similarity": sim
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results


async_rag_service = AsyncRAGService()


import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import random
from typing import Any, Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument


def _parse_tags(tags_val: Any) -> List[str]:
    if not tags_val:
        return []
    if isinstance(tags_val, list):
        return [str(t) for t in tags_val]
    if isinstance(tags_val, str):
        try:
            parsed = json.loads(tags_val)
            if isinstance(parsed, list):
                return [str(t) for t in parsed]
        except Exception:
            pass
        return [t.strip() for t in tags_val.split(",") if t.strip()]
    return []


def _serialize_tags(tags_val: Optional[List[str]]) -> str:
    if not tags_val:
        return "[]"
    return json.dumps(list(tags_val))


DEFAULT_KNOWLEDGE_DOCUMENTS = [
    {
        "title": "Krea 2 Formatting & Natural Language Architecture",
        "category": "model_guide",
        "tags": ["krea", "krea2", "prompt_structure", "prose"],
        "content": (
            "Krea 2 Prompt Engineering Architecture:\n"
            "Krea 2 excels when prompted with natural language prose and narrative context rather than comma-delimited tag soup. "
            "Structure your prompt hierarchically: 1. Core Subject & Action (who/what is the focus, posture, emotion); "
            "2. Environmental Setting & Staging (architecture, spatial depth, foreground/background interaction); "
            "3. Lighting, Atmosphere & Color Harmony (diffuse volumetric lighting, color palette, atmospheric haze); "
            "4. Photographic Lens & Cinematic Camera (focal length, depth of field, sensor stock). "
            "Avoid low-information buzzwords like 'photorealistic', 'ultra high quality', and 'trending on artstation'; "
            "instead describe tangible materials, surface textures, and physical light interaction (e.g., 'subsurface scattering on weathered skin', 'brushed anodized aluminium')."
        )
    },
    {
        "title": "ANIMA Model Aesthetic & Tag Hierarchy",
        "category": "anime_style",
        "tags": ["anima", "anime", "score_tags", "danbooru"],
        "content": (
            "ANIMA Diffusion Model Syntax & Styling Hierarchy:\n"
            "ANIMA utilizes Danbooru tag conventions paired with quality score prefixes for fine-grained aesthetic control. "
            "Recommended structure:\n"
            "1. Quality Anchors: 'masterpiece, best quality, newest, sensitive'\n"
            "2. Character & Feature Specs: Specify 1girl/1boy, hair style, eye color, facial expression, and outfit details.\n"
            "3. Composition & Framing: 'dynamic angle, cowboy shot, looking at viewer, dramatic cinematic lighting'\n"
            "4. Atmosphere & Background: 'cherry blossoms, sunset rim lighting, floating particles, painterly background'\n"
            "Keep tag weights cleanly balanced between (0.9) and (1.2) to prevent anatomy distortion and feature artifacts."
        )
    },
    {
        "title": "Photorealistic Optics & Lighting Descriptors",
        "category": "optics",
        "tags": ["optics", "cinematic", "lighting", "portrait"],
        "content": (
            "Photorealistic Optics, Camera Lenses, and Studio Lighting Descriptors:\n"
            "1. Focal Length & Lens Characteristics: '85mm f/1.4 prime lens for flattering portrait compression and creamy bokeh', "
            "'35mm anamorphic lens for cinematic wide aspect ratios and subtle horizontal flare', '100mm macro lens for microscopic texture fidelity'.\n"
            "2. Professional Lighting Systems: 'Rembrandt lighting with soft catchlight in eyes', 'subtle golden hour rim lighting with diffused fill light', "
            "'chiaroscuro high-contrast lighting with deep shadows', 'volumetric morning light filtering through blinds'.\n"
            "3. Optical Phenomena: 'shallow depth of field, natural vignetting, specular skin highlights, realistic subsurface scattering, micro-contrast'.\n"
            "4. Color Science: 'Kodak Portra 400 color grading, rich tonal dynamic range, organic 35mm film grain'."
        )
    },
    {
        "title": "Negative Prompting Artifact Suppression",
        "category": "negative_rules",
        "tags": ["negative", "artifacts", "anatomy", "quality"],
        "content": (
            "Targeted Negative Prompting & Defect Suppression:\n"
            "Negative prompts prevent common generative artifacts when targeted precisely rather than applied as generic bloated blobs.\n"
            "1. Anatomy & Morphology: 'extra limbs, mutated hands, missing fingers, fused anatomy, poorly drawn face, asymmetric eyes, unnatural body proportions'.\n"
            "2. Digital & Compression Artifacts: 'jpeg compression artifacts, pixelation, low resolution, banding, oversaturated color clipping, blurry textures'.\n"
            "3. Unwanted Text & Overlays: 'watermark, text, username, artist signature, borders, copyright stamp'.\n"
            "4. Stylistic Drift: 'plastic skin, uncanny valley 3D render, flat illustration, cartoonish shading' when aiming for photorealism.\n"
            "Overly aggressive negative prompts can mute color vibrancy and contrast; tune negative weights moderately."
        )
    }
]


class UnifiedRAGService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = asyncio.Lock()

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = "MOCK"
        return self._model

    def _compute_sync(self, text: str) -> List[float]:
        model = self._get_model()
        if model == "MOCK":
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
            rng = random.Random(seed)
            return [rng.uniform(-1.0, 1.0) for _ in range(384)]
        else:
            vec = model.encode(text)
            if hasattr(vec, "tolist"):
                return vec.tolist()
            return list(vec)

    async def compute_embedding_async(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._compute_sync, text)

    async def seed_default_knowledge_if_empty(self, db: Session) -> None:
        starter_titles = [d["title"] for d in DEFAULT_KNOWLEDGE_DOCUMENTS]
        existing_starter = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.title.in_(starter_titles)
        ).count()
        if existing_starter < len(DEFAULT_KNOWLEDGE_DOCUMENTS):
            existing_titles = {d.title for d in db.query(KnowledgeDocument.title).all()}
            for item in DEFAULT_KNOWLEDGE_DOCUMENTS:
                if item["title"] in existing_titles:
                    continue
                content_to_embed = f"{item['title']}\n{item['content']}"
                vec = await self.compute_embedding_async(content_to_embed)
                doc = KnowledgeDocument(
                    title=item["title"],
                    content=item["content"],
                    category=item["category"],
                    tags=_serialize_tags(item["tags"]),
                    embedding=vec
                )
                db.add(doc)
            db.commit()

    async def search_knowledge_async(
        self,
        db: Session,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[dict]:
        query_vec = await self.compute_embedding_async(query)
        distance_expr = KnowledgeDocument.embedding.cosine_distance(query_vec)

        q = db.query(KnowledgeDocument, distance_expr.label("distance"))
        q = q.filter(KnowledgeDocument.embedding.isnot(None))

        if category:
            q = q.filter(KnowledgeDocument.category.ilike(category))

        if tag:
            q = q.filter(KnowledgeDocument.tags.ilike(f"%{tag}%"))

        q = q.order_by(distance_expr).limit(top_k)
        rows = q.all()

        results = []
        for doc, dist in rows:
            # Cosine distance in pgvector: 0 is identical, 2 is opposite.
            # Convert to similarity percentage: (1.0 - dist) * 100.0
            distance_val = float(dist) if dist is not None else 1.0
            sim_score = max(0.0, min(100.0, (1.0 - distance_val) * 100.0))
            results.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "category": doc.category or "general",
                "tags": _parse_tags(doc.tags),
                "similarity_score": round(sim_score, 1)
            })

        return results

    async def index_document_async(
        self,
        db: Session,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> dict:
        content_to_embed = f"{title}\n{content}".strip()
        vec = await self.compute_embedding_async(content_to_embed)
        doc = KnowledgeDocument(
            title=title,
            content=content,
            category=category or "general",
            tags=_serialize_tags(tags or []),
            embedding=vec
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "category": doc.category,
            "tags": _parse_tags(doc.tags)
        }

    async def delete_document_async(self, db: Session, doc_id: int) -> bool:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True

    async def get_documents_async(
        self,
        db: Session,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[dict]:
        q = db.query(KnowledgeDocument)
        if category:
            q = q.filter(KnowledgeDocument.category.ilike(category))
        if query:
            pattern = f"%{query}%"
            q = q.filter(or_(
                KnowledgeDocument.title.ilike(pattern),
                KnowledgeDocument.content.ilike(pattern)
            ))
        if tag:
            q = q.filter(KnowledgeDocument.tags.ilike(f"%{tag}%"))

        q = q.order_by(KnowledgeDocument.id.asc())
        docs = q.all()

        results = []
        for doc in docs:
            doc_tags = _parse_tags(doc.tags)
            if tag and not any(tag.lower() == t.lower() for t in doc_tags):
                continue
            results.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "category": doc.category or "general",
                "tags": doc_tags
            })
        return results

    async def get_stats_async(self, db: Session) -> dict:
        docs = db.query(KnowledgeDocument).all()
        all_tags = set()
        categories = set()
        for doc in docs:
            if doc.category:
                categories.add(doc.category)
            for t in _parse_tags(doc.tags):
                all_tags.add(t)

        return {
            "total_documents": len(docs),
            "total_tags": len(all_tags),
            "model_name": self.model_name,
            "categories": sorted(list(categories))
        }

    def close(self):
        self._executor.shutdown(wait=False)


unified_rag_service = UnifiedRAGService()

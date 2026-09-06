"""
Danbooru Lexicon & Co-occurrence Recommendation Service
Provides sub-millisecond queries for 31,000+ Danbooru tags and 3.2M co-occurrence pairs.
"""

import os
import sqlite3
import re
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from app.models.tag import Tag


class DanbooruService:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            candidates = [
                os.environ.get("DANBOORU_DB_PATH", ""),
                os.path.join(os.path.dirname(__file__), "..", "data", "danbooru_lexicon.db"),
                os.path.join(os.getcwd(), "backend", "app", "data", "danbooru_lexicon.db"),
                "/app/app/data/danbooru_lexicon.db",
                "backend/app/data/danbooru_lexicon.db",
            ]
            self.db_path = ""
            for c in candidates:
                if c and os.path.exists(c):
                    self.db_path = os.path.abspath(c)
                    break
            if not self.db_path:
                self.db_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "data", "danbooru_lexicon.db")
                )

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def is_ready(self) -> bool:
        if not os.path.exists(self.db_path):
            return False
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM danbooru_tags")
            count = cur.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        if not self.is_ready():
            return {
                "ready": False,
                "total_tags": 0,
                "total_cooccurrences": 0,
                "db_size_mb": 0.0,
                "categories": []
            }

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM danbooru_tags")
        total_tags = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM cooccurrences")
        total_cooc = cur.fetchone()[0]

        cur.execute("SELECT category, COUNT(*) as cnt FROM danbooru_tags GROUP BY category ORDER BY cnt DESC")
        cats = [{"category": row["category"], "count": row["cnt"]} for row in cur.fetchall()]

        conn.close()

        size_mb = 0.0
        if os.path.exists(self.db_path):
            size_mb = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)

        return {
            "ready": True,
            "total_tags": total_tags,
            "total_cooccurrences": total_cooc,
            "db_size_mb": size_mb,
            "categories": cats
        }

    def get_tags(
        self,
        q: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.is_ready():
            return []

        conn = self._get_connection()
        cur = conn.cursor()

        conditions = []
        params = []

        if q:
            clean_q = q.strip().lower().replace(" ", "_")
            conditions.append("tag LIKE ?")
            params.append(f"%{clean_q}%")

        if category and category.lower() != "all":
            conditions.append("LOWER(category) = ?")
            params.append(category.lower())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT tag, category, total_count
            FROM danbooru_tags
            {where_clause}
            ORDER BY total_count DESC
            LIMIT ? OFFSET ?
        """
        params.extend([min(limit, 500), max(offset, 0)])

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "tag": r["tag"],
                "category": r["category"],
                "total_count": r["total_count"]
            }
            for r in rows
        ]

    def get_cooccurrences(self, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.is_ready() or not tag:
            return []

        clean_tag = tag.strip().lower().replace(" ", "_")
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.tag_b AS related_tag, d.category, c.count
            FROM cooccurrences c
            LEFT JOIN danbooru_tags d ON c.tag_b = d.tag
            WHERE c.tag_a = ?
            ORDER BY c.count DESC
            LIMIT ?
            """,
            (clean_tag, limit)
        )
        rows = cur.fetchall()

        if len(rows) < limit:
            remaining = limit - len(rows)
            seen = {r["related_tag"] for r in rows}
            cur.execute(
                """
                SELECT c.tag_a AS related_tag, d.category, c.count
                FROM cooccurrences c
                LEFT JOIN danbooru_tags d ON c.tag_a = d.tag
                WHERE c.tag_b = ?
                ORDER BY c.count DESC
                LIMIT ?
                """,
                (clean_tag, remaining * 2)
            )
            for r in cur.fetchall():
                if r["related_tag"] not in seen:
                    seen.add(r["related_tag"])
                    rows.append(r)
                if len(rows) >= limit:
                    break

        conn.close()

        return [
            {
                "tag": r["related_tag"],
                "category": r["category"] or "general",
                "count": r["count"]
            }
            for r in rows[:limit]
        ]

    def recommend_tags(
        self,
        prompt: Optional[str] = None,
        current_tags: Optional[List[str]] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        if not self.is_ready():
            return []

        input_tokens: Set[str] = set()
        if current_tags:
            for t in current_tags:
                clean = t.strip().lower().replace(" ", "_")
                if clean:
                    input_tokens.add(clean)

        if prompt:
            parts = re.split(r"[,|\n]", prompt)
            for p in parts:
                p_clean = re.sub(r"[\(\)\[\]\{\}]", "", p)
                p_clean = re.sub(r":\d+(?:\.\d+)?", "", p_clean).strip().lower().replace(" ", "_")
                if p_clean and not p_clean.startswith("__"):
                    input_tokens.add(p_clean)

        if not input_tokens:
            top_tags = self.get_tags(limit=limit)
            return [
                {
                    "tag": t["tag"],
                    "category": t["category"],
                    "score": t["total_count"],
                    "reason": "Top Popular Tag"
                }
                for t in top_tags
            ]

        candidate_scores: Dict[str, float] = {}
        candidate_reasons: Dict[str, str] = {}

        conn = self._get_connection()
        cur = conn.cursor()

        for token in input_tokens:
            cur.execute(
                """
                SELECT tag_b, count
                FROM cooccurrences
                WHERE tag_a = ?
                ORDER BY count DESC
                LIMIT 40
                """,
                (token,)
            )
            for r in cur.fetchall():
                rel = r["tag_b"]
                if rel in input_tokens:
                    continue
                cnt = r["count"]
                candidate_scores[rel] = candidate_scores.get(rel, 0.0) + cnt
                if rel not in candidate_reasons:
                    candidate_reasons[rel] = f"Pairs with {token}"

        top_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        if not top_candidates:
            conn.close()
            return []

        cand_tags = [c[0] for c in top_candidates]
        placeholders = ",".join(["?"] * len(cand_tags))
        cur.execute(f"SELECT tag, category FROM danbooru_tags WHERE tag IN ({placeholders})", cand_tags)
        cat_map = {r["tag"]: r["category"] for r in cur.fetchall()}
        conn.close()

        results = []
        for tag_name, score in top_candidates:
            results.append({
                "tag": tag_name,
                "category": cat_map.get(tag_name, "general"),
                "score": round(score, 1),
                "reason": candidate_reasons.get(tag_name, "High synergy")
            })

        return results

    def import_to_postgres(self, db: Session, limit: int = 5000) -> Dict[str, Any]:
        if not self.is_ready():
            return {"imported": 0, "already_existing": 0, "error": "Danbooru DB not ready"}

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tag, category, total_count
            FROM danbooru_tags
            ORDER BY total_count DESC
            LIMIT ?
            """,
            (limit,)
        )
        candidates = cur.fetchall()
        conn.close()

        CAT_MAP = {
            "artist": "Artist",
            "character": "Character",
            "copyright": "Style",
            "meta": "Quality / Score",
            "general": "General"
        }

        existing_tags = {t.name.lower(): t for t in db.query(Tag).all()}

        new_tags = []
        already_count = 0

        for row in candidates:
            tag_name = row["tag"].replace("_", " ")
            if tag_name.lower() in existing_tags:
                already_count += 1
                continue
            cat = CAT_MAP.get(row["category"].lower(), "General")
            new_tags.append(Tag(name=tag_name, category=cat))

        if new_tags:
            db.bulk_save_objects(new_tags)
            db.commit()

        return {
            "imported": len(new_tags),
            "already_existing": already_count,
            "total_requested": limit
        }


danbooru_service = DanbooruService()
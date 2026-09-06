import itertools
import random
# CRITICAL: Always ensure 'Any' (and List/Dict) are imported from typing for type annotations to prevent FastAPI Uvicorn startup crashes
from typing import List, Dict, Any, Optional
from app.services.wildcard_ast import (
    WildcardASTEngine, ASTNode, RootNode, TextNode, WildcardNode, ChoiceNode, ChoiceOption
)

class MatrixEngine:
    DEFAULT_SAFE_LIMIT: int = 20000
    MAX_ALLOWED_LIMIT: int = 100000

    def __init__(self, wildcards: Dict[str, List[str]] = None, max_limit: Optional[int] = None):
        self.wildcards = wildcards or {}
        self.max_limit = max_limit
        self.ast_engine = WildcardASTEngine(self.wildcards)

    def _resolve_limit(self, max_limit: Optional[int]) -> int:
        """Determines safe permutation limit, enforcing ceilings to prevent memory exhaustion."""
        candidate = max_limit if max_limit is not None else self.max_limit
        if candidate is None or candidate <= 0:
            return self.DEFAULT_SAFE_LIMIT
        return min(candidate, self.MAX_ALLOWED_LIMIT)

    def generate_matrix(self, prompt: str, max_depth: int = 10, expand_wildcards: bool = True, max_limit: Optional[int] = None) -> List[str]:
        """Generates Cartesian product combinations of the prompt up to a safe limit to prevent memory exhaustion."""
        limit = self._resolve_limit(max_limit)
        ast = self.ast_engine.parse(prompt)
        combos = self._get_node_combinations(ast, max_depth=max_depth, current_depth=0, expand_wildcards=expand_wildcards, limit=limit)
        
        # Deduplicate while preserving order, capped at limit
        seen = set()
        unique_combos = []
        for item in combos:
            if item not in seen:
                seen.add(item)
                unique_combos.append(item)
                if len(unique_combos) >= limit:
                    break
        return unique_combos

    def get_wildcard_entries(self, name: str) -> Optional[List[str]]:
        """Smart resolution of wildcard names across exact match, case insensitivity, directory stripping, and fuzzy stems."""
        return self.ast_engine.get_wildcard_entries(name)

    def _get_node_combinations(self, node: ASTNode, max_depth: int, current_depth: int, expand_wildcards: bool = True, limit: int = DEFAULT_SAFE_LIMIT) -> List[str]:
        if current_depth >= max_depth:
            return [self.ast_engine._unexpanded_str(node)]

        if isinstance(node, TextNode):
            return [node.text]

        elif isinstance(node, RootNode):
            if not node.children:
                return [""]
            
            child_combos = [
                self._get_node_combinations(child, max_depth, current_depth, expand_wildcards=expand_wildcards, limit=limit)
                for child in node.children
            ]
            
            results = []
            for combo_tuple in itertools.product(*child_combos):
                results.append("".join(combo_tuple))
                if limit and limit > 0 and len(results) >= limit * 2:
                    break
            return results

        elif isinstance(node, ChoiceNode):
            combos = []
            for option in node.options:
                opt_combos = self._get_node_combinations(option.content, max_depth, current_depth, expand_wildcards=expand_wildcards, limit=limit)
                combos.extend(opt_combos)
                if limit and limit > 0 and len(combos) >= limit * 2:
                    break
            return combos

        elif isinstance(node, WildcardNode):
            name = node.name
            entries = self.get_wildcard_entries(name)
            if expand_wildcards and entries:
                combos = []
                # Performance optimization: if wildcard has 50,000 entries and limit is 1,000,
                # slicing entries up to limit * 2 prevents parsing 50,000 ASTs
                slice_cap = limit * 2 if limit and limit > 0 else len(entries)
                target_entries = entries[:slice_cap] if len(entries) > slice_cap else entries
                for entry in target_entries:
                    entry_ast = self.ast_engine.parse(entry)
                    entry_combos = self._get_node_combinations(entry_ast, max_depth, current_depth + 1, expand_wildcards=expand_wildcards, limit=limit)
                    combos.extend(entry_combos)
                    if limit and limit > 0 and len(combos) >= limit * 2:
                        break
                return combos
            else:
                return [f"__{name}__"]

        return [""]

    def analyze_heatmap_scores(self, prompt: str, expand_wildcards: bool = True, max_limit: Optional[int] = None) -> Dict[str, Any]:
        """Analyzes matrix sweep combinations for CLIP token distributions and Danbooru tag category proportions."""
        heatmap_limit = min(max_limit or 500, 2000)
        combos = self.generate_matrix(prompt, expand_wildcards=expand_wildcards, max_limit=heatmap_limit)
        category_counts: Dict[str, int] = {
            "artist": 0,
            "character": 0,
            "copyright": 0,
            "general": 0,
            "meta": 0
        }
        token_lengths: List[int] = []

        for combo in combos:
            tokens = [t.strip() for t in combo.split(',') if t.strip()]
            token_lengths.append(len(tokens))
            categorized = self.ast_engine.categorize_danbooru_tags(combo)
            for cat_item in categorized:
                cat = cat_item.get("category", "general")
                category_counts[cat] = category_counts.get(cat, 0) + 1

        avg_token_count = round(sum(token_lengths) / len(token_lengths), 2) if token_lengths else 0.0

        return {
            "combinations_count": len(combos),
            "avg_token_count": avg_token_count,
            "min_token_count": min(token_lengths) if token_lengths else 0,
            "max_token_count": max(token_lengths) if token_lengths else 0,
            "category_distribution": category_counts
        }

    def count_permutations(self, prompt: str, expand_wildcards: bool = True) -> int:
        """Calculates exact total number of combinatorial permutations without generating all prompts in memory."""
        ast = self.ast_engine.parse(prompt)
        return self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)

    def get_matrix_slice(self, prompt: str, offset: int = 0, limit: int = 50, expand_wildcards: bool = True) -> Dict[str, Any]:
        """Retrieves a paginated slice of matrix combinations via direct indexing in O(1) time without generating the full Cartesian product."""
        ast = self.ast_engine.parse(prompt)
        total_count = self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)

        safe_offset = max(0, offset)
        safe_limit = max(0, limit)
        end_idx = min(safe_offset + safe_limit, total_count)

        items = []
        for idx in range(safe_offset, end_idx):
            prompt_str = self.ast_engine.get_permutation_at_index(ast, idx, expand_wildcards=expand_wildcards)
            items.append({
                "index": idx + 1,  # 1-based index
                "prompt": prompt_str
            })

        return {
            "total_count": total_count,
            "offset": safe_offset,
            "limit": safe_limit,
            "items": items,
            "is_sample": False
        }

    def get_matrix_sample(self, prompt: str, sample_size: int = 25, seed: Optional[int] = None, expand_wildcards: bool = True) -> Dict[str, Any]:
        """Retrieves a deterministic or random uniform sample of matrix combinations across the entire parameter space."""
        ast = self.ast_engine.parse(prompt)
        total_count = self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)

        safe_sample_size = max(0, sample_size)
        if total_count == 0 or safe_sample_size == 0:
            return {
                "total_count": total_count,
                "sample_size": safe_sample_size,
                "items": [],
                "is_sample": True
            }

        rng = random.Random(seed) if seed is not None else random.Random()
        k = min(safe_sample_size, total_count)
        sampled_indices = sorted(rng.sample(range(total_count), k))

        items = []
        for idx in sampled_indices:
            prompt_str = self.ast_engine.get_permutation_at_index(ast, idx, expand_wildcards=expand_wildcards)
            items.append({
                "index": idx + 1,  # 1-based index
                "prompt": prompt_str
            })

        return {
            "total_count": total_count,
            "sample_size": safe_sample_size,
            "items": items,
            "is_sample": True
        }


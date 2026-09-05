import re
from typing import Dict, List, Set, Tuple

class WildcardGraph:
    def __init__(self, wildcards: Dict[str, List[str]]):
        self.wildcards = wildcards
        self.graph: Dict[str, Set[str]] = {}
        self.missing: Set[str] = set()
        self.cycles: List[List[str]] = []
        
        self._build_graph()
        self._detect_cycles()

    def _build_graph(self):
        """Builds a directed graph mapping wildcards to their dependencies."""
        for wildcard_name, entries in self.wildcards.items():
            dependencies = set()
            for entry in entries:
                # Find all __wildcard__ references
                matches = re.findall(r'__([a-zA-Z0-9_/\-]+)__', entry)
                for match in matches:
                    dependencies.add(match)
                    if match not in self.wildcards:
                        self.missing.add(match)
            self.graph[wildcard_name] = dependencies

    def _detect_cycles(self):
        """Detects circular dependencies using Depth-First Search."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in self.graph:
                for neighbor in self.graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor)
                    elif neighbor in rec_stack:
                        # Cycle detected
                        cycle_start_index = path.index(neighbor)
                        self.cycles.append(path[cycle_start_index:] + [neighbor])

            rec_stack.remove(node)
            path.pop()

        for node in self.graph:
            if node not in visited:
                dfs(node)

    def get_validation_report(self) -> Dict:
        return {
            "is_valid": len(self.cycles) == 0 and len(self.missing) == 0,
            "cycles": self.cycles,
            "missing": list(self.missing),
            "graph": {k: list(v) for k, v in self.graph.items()}
        }

class TagGraphService:
    def __init__(self):
        from collections import defaultdict
        self.co_occurrences: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def add_cooccurrence(self, tags: List[str]):
        clean_tags = [t.strip().lower() for t in tags if t.strip()]
        for i in range(len(clean_tags)):
            for j in range(i + 1, len(clean_tags)):
                t1, t2 = clean_tags[i], clean_tags[j]
                if t1 != t2:
                    self.co_occurrences[t1][t2] += 1
                    self.co_occurrences[t2][t1] += 1

    def recommend(self, input_tags: List[str], top_k: int = 5) -> List[str]:
        from collections import Counter
        scores = Counter()
        clean_inputs = set(t.strip().lower() for t in input_tags if t.strip())
        
        for tag in clean_inputs:
            if tag in self.co_occurrences:
                for neighbor, weight in self.co_occurrences[tag].items():
                    if neighbor not in clean_inputs:
                        scores[neighbor] += weight

        return [tag for tag, _ in scores.most_common(top_k)]


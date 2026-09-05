from collections import Counter
from typing import Dict, List
from app.services.wildcard_engine import WildcardEngine
from app.services.wildcard_graph import WildcardGraph

class Simulator:
    def __init__(self, engine: WildcardEngine):
        self.engine = engine

    def run_simulation(self, template: str, iterations: int = 100) -> Dict:
        """
        Runs Monte Carlo simulation on a prompt template.
        Returns the frequency distribution of generated outputs.
        """
        # 1. Validate first to avoid infinite loops during simulation
        graph = WildcardGraph(self.engine.wildcards)
        report = graph.get_validation_report()
        if len(report.get("cycles", [])) > 0:
            return {
                "success": False,
                "error": "Validation failed: Circular dependencies found.",
                "validation_report": report
            }
            
        counter = Counter()
        for _ in range(iterations):
            # We use max_depth to prevent infinite loops in edge cases
            result = self.engine.expand_prompt(template, max_depth=20)
            counter[result] += 1
            
        results = []
        for text, count in counter.most_common():
            results.append({
                "text": text,
                "count": count,
                "percentage": round((count / iterations) * 100, 2)
            })
            
        return {
            "success": True,
            "iterations": iterations,
            "unique_results": len(counter),
            "distribution": results,
            "validation_report": report
        }

    def build_ast_tree(self, template: str) -> Dict:
        """
        Parses template into AST node hierarchy for UI visualization.
        """
        from app.services.wildcard_ast import WildcardASTEngine
        ast_engine = WildcardASTEngine()
        root = ast_engine.parse(template)
        
        def node_to_dict(node):
            if hasattr(node, "content"):
                return {"type": "text", "label": node.content}
            elif hasattr(node, "name"):
                return {"type": "wildcard", "label": f"__{node.name}__"}
            elif hasattr(node, "options"):
                children = [node_to_dict(opt) for opt in node.options]
                return {"type": "choice", "label": "Choice", "children": children}
            elif hasattr(node, "children"):
                children = [node_to_dict(child) for child in node.children]
                return {"type": "root", "label": "Root", "children": children}
            return {"type": "unknown", "label": str(node)}

        return {
            "template": template,
            "tree": node_to_dict(root)
        }


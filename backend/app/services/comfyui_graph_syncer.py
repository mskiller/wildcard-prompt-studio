from typing import Dict, Any, List

class ComfyUIGraphSyncer:
    """Service to inspect and map dynamic inputs in ComfyUI workflow JSON graphs."""

    def inspect_graph(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        nodes = []
        prompt_nodes = []
        sampler_nodes = []

        for node_id, node_data in workflow_json.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            meta = node_data.get("_meta")
            if isinstance(meta, dict):
                meta_title = meta.get("title", class_type)
            else:
                meta_title = class_type

            inputs = node_data.get("inputs", {})
            input_keys = list(inputs.keys()) if isinstance(inputs, dict) else []

            node_info = {
                "node_id": str(node_id),
                "class_type": class_type,
                "title": meta_title,
                "inputs": input_keys
            }
            nodes.append(node_info)

            if "CLIPTextEncode" in class_type or "Text" in class_type:
                prompt_nodes.append(node_info)
            elif "KSampler" in class_type or "Sampler" in class_type:
                sampler_nodes.append(node_info)

        return {
            "nodes": nodes,
            "prompt_nodes": prompt_nodes,
            "sampler_nodes": sampler_nodes
        }

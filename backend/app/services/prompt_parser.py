import yaml

def parse_prompt_file(content: str) -> dict:
    parts = content.split("---", 1)
    
    metadata = {}
    body_text = content
    
    if len(parts) == 2:
        # We have frontmatter
        try:
            metadata = yaml.safe_load(parts[0].strip()) or {}
        except yaml.YAMLError:
            metadata = {}
        body_text = parts[1].strip()
        
    try:
        sections = yaml.safe_load(body_text) or {}
        if not isinstance(sections, dict):
            sections = {"content": body_text}
    except yaml.YAMLError:
        sections = {"content": body_text}
        
    return {
        "metadata": metadata,
        "sections": sections
    }

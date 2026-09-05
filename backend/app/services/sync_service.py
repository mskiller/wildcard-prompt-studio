import os
import yaml
import logging
from app.models.prompt import Prompt
from app.models.wildcard import Wildcard
from app.database import SessionLocal

logger = logging.getLogger(__name__)
_default_ws = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspace"))
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR") or (_default_ws if not os.path.exists("/workspace") else "/workspace")

def export_prompt_to_file(prompt: Prompt):
    """Writes a Prompt object to a .prompt file."""
    try:
        if not prompt.name:
            return
            
        filepath = os.path.join(WORKSPACE_DIR, "prompts", f"{prompt.name}.prompt")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        metadata = {}
        if prompt.name: metadata["name"] = prompt.name
        if prompt.author: metadata["author"] = prompt.author
        if prompt.license: metadata["license"] = prompt.license
        if prompt.theme: metadata["theme"] = prompt.theme
        
        with open(filepath, "w", encoding="utf-8") as f:
            if metadata:
                f.write(yaml.dump(metadata, sort_keys=False).strip() + "\n")
                f.write("---\n")
            f.write(prompt.content)
            
        logger.info(f"Exported prompt to {filepath}")
    except Exception as e:
        logger.error(f"Failed to export prompt {prompt.id}: {e}")

def export_wildcard_to_file(wildcard: Wildcard):
    """Writes a Wildcard object to a file."""
    try:
        filename = wildcard.filename
        if not filename.endswith(f".{wildcard.type}"):
            filename = f"{filename}.{wildcard.type}"
            
        filepath = os.path.join(WORKSPACE_DIR, "wildcards", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(wildcard.content)
            
        logger.info(f"Exported wildcard to {filepath}")
    except Exception as e:
        logger.error(f"Failed to export wildcard {wildcard.id}: {e}")

def handle_file_sync(filepath: str, event_type: str):
    """
    Called by Celery worker when a file is modified externally.
    Syncs the file contents back to the database.
    """
    logger.info(f"Processing sync for {filepath} ({event_type})")
    if not os.path.exists(filepath) and event_type != "deleted":
        return
        
    db = SessionLocal()
    try:
        # TODO: Implement parsing and saving to DB based on filepath
        # e.g., if filepath.endswith(".prompt"), parse and update Prompt table
        pass
    finally:
        db.close()

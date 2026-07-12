from app.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from app.services.wildcard_engine import WildcardEngine
from app.services.comfyui_connector import ComfyUIConnector

wildcard_engine_instance = None
comfyui_connector_instance = None

def get_wildcard_engine() -> WildcardEngine:
    global wildcard_engine_instance
    if wildcard_engine_instance is None:
        wildcard_engine_instance = WildcardEngine()
        # Ensure it loads from the correct wildcards directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wildcards_dir = os.path.join(base_dir, "wildcards")
        wildcard_engine_instance.load_from_directory(wildcards_dir)
    return wildcard_engine_instance

def get_comfyui_connector() -> ComfyUIConnector:
    global comfyui_connector_instance
    if comfyui_connector_instance is None:
        comfyui_connector_instance = ComfyUIConnector()
    return comfyui_connector_instance

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

from app.services.krea2_optimizer import Krea2Optimizer
from app.services.anima_optimizer import AnimaOptimizer
from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.kobold_provider import KoboldCppProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.matrix_engine import MatrixEngine
from fastapi import Depends

krea2_optimizer_instance = None
anima_optimizer_instance = None
provider_manager_instance = None

def get_krea2_optimizer() -> Krea2Optimizer:
    global krea2_optimizer_instance
    if krea2_optimizer_instance is None:
        krea2_optimizer_instance = Krea2Optimizer()
    return krea2_optimizer_instance

def get_anima_optimizer() -> AnimaOptimizer:
    global anima_optimizer_instance
    if anima_optimizer_instance is None:
        anima_optimizer_instance = AnimaOptimizer()
    return anima_optimizer_instance


def get_provider_manager() -> AIProviderManager:
    global provider_manager_instance
    if provider_manager_instance is None:
        provider_manager_instance = AIProviderManager()
        if "kobold" not in provider_manager_instance.list_providers():
            provider_manager_instance.register_provider("kobold", KoboldCppProvider())
        if "ollama" not in provider_manager_instance.list_providers():
            provider_manager_instance.register_provider("ollama", OllamaProvider())
    return provider_manager_instance

from sqlalchemy.orm import Session

def get_matrix_engine(
    engine: WildcardEngine = Depends(get_wildcard_engine),
    db: Session = Depends(get_db)
) -> MatrixEngine:
    wildcards_dict = dict(engine.wildcards)
    try:
        from app.models.wildcard import Wildcard
        db_wildcards = db.query(Wildcard).all()
        for w in db_wildcards:
            clean_name = w.filename.replace('.txt', '').replace('.yaml', '').replace('.yml', '')
            lines = []
            if w.entries and isinstance(w.entries, list) and len(w.entries) > 0:
                lines = [str(x).strip() for x in w.entries if str(x).strip()]
            elif w.content:
                lines = [l.strip() for l in w.content.splitlines() if l.strip() and not l.startswith('#')]

            if lines:
                wildcards_dict[clean_name] = lines
                wildcards_dict[w.filename] = lines
                wildcards_dict[clean_name.lower()] = lines
                if '/' in clean_name or '\\' in clean_name:
                    basename = clean_name.replace('\\', '/').split('/')[-1]
                    wildcards_dict[basename] = lines
                    wildcards_dict[basename.lower()] = lines
                else:
                    # Also register common subfolder prefixes for convenience (e.g. mskiller/name)
                    wildcards_dict[f"mskiller/{clean_name}"] = lines
                    wildcards_dict[f"mskiller/{clean_name.lower()}"] = lines

        # Also load from /workspace/wildcards if present
        workspace_wc_dir = "/workspace/wildcards"
        if not os.path.exists(workspace_wc_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workspace_wc_dir = os.path.join(base_dir, "workspace", "wildcards")
        if os.path.exists(workspace_wc_dir):
            for root, _, files in os.walk(workspace_wc_dir):
                for f in files:
                    if f.endswith('.txt') or f.endswith('.yaml') or f.endswith('.yml'):
                        fn_clean = os.path.splitext(f)[0]
                        if fn_clean not in wildcards_dict:
                            fp = os.path.join(root, f)
                            try:
                                with open(fp, 'r', encoding='utf-8') as fh:
                                    flines = [l.strip() for l in fh if l.strip() and not l.startswith('#')]
                                    if flines:
                                        wildcards_dict[fn_clean] = flines
                                        wildcards_dict[fn_clean.lower()] = flines
                                        wildcards_dict[f"mskiller/{fn_clean}"] = flines
                                        wildcards_dict[f"mskiller/{fn_clean.lower()}"] = flines
                            except Exception:
                                pass
    except Exception:
        pass
    return MatrixEngine(wildcards=wildcards_dict)



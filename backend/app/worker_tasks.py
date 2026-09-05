from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

# Lazily load the sentence transformer model so it doesn't block worker startup
_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder

@celery_app.task
def sync_file_to_db(filepath: str, event_type: str):
    """
    Syncs a file from the workspace to the database.
    event_type can be 'created', 'modified', or 'deleted'
    """
    logger.info(f"Received sync task for file: {filepath} with event: {event_type}")
    
    from app.services.sync_service import handle_file_sync
    handle_file_sync(filepath, event_type)

@celery_app.task
def generate_prompt_embedding(prompt_id: int):
    """
    Generates a semantic embedding vector for a prompt.
    """
    logger.info(f"Generating embedding for prompt {prompt_id}")
    from app.database import SessionLocal
    from app.models.prompt import Prompt
    
    db = SessionLocal()
    try:
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt or not prompt.content:
            return
            
        model = get_embedder()
        embedding = model.encode(prompt.content)
        prompt.embedding = embedding.tolist()
        
        db.commit()
        logger.info(f"Successfully saved embedding for prompt {prompt_id}")
    except Exception as e:
        logger.error(f"Failed to generate embedding for prompt {prompt_id}: {e}")
        db.rollback()
    finally:
        db.close()

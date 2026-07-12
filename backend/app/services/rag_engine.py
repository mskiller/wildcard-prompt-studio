from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument

def search_knowledge(db_session: Session, query_embedding: list[float], limit: int = 3):
    """
    Search for knowledge documents closest to the query embedding.
    """
    return db_session.query(KnowledgeDocument).order_by(
        KnowledgeDocument.embedding.l2_distance(query_embedding)
    ).limit(limit).all()

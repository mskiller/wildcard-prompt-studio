from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger, Boolean, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Image(Base):
    """Generated image record with metadata, ratings, aesthetic score, and prompt linkage."""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
    
    seed = Column(BigInteger, nullable=True)
    cfg_scale = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    sampler_name = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    comfy_workflow_id = Column(String, nullable=True)
    
    is_favorite = Column(Boolean, default=False, server_default=text('false'), index=True)
    rating = Column(Integer, default=0, server_default=text('0'), index=True)
    aesthetic_score = Column(Float, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    prompt = relationship("Prompt", back_populates="images")

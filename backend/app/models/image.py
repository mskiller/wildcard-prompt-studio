from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    
    seed = Column(BigInteger, nullable=True)
    cfg_scale = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    sampler_name = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    comfy_workflow_id = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prompt = relationship("Prompt", back_populates="images")

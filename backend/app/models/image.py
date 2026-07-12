from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

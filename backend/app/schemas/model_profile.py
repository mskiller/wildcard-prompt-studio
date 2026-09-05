from pydantic import BaseModel
from typing import Optional

class ModelProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    default_negative_prompt: Optional[str] = None
    trigger_words: Optional[str] = None
    custom_rules: Optional[str] = None

class ModelProfileCreate(ModelProfileBase):
    pass

class ModelProfileUpdate(ModelProfileBase):
    name: Optional[str] = None

class ModelProfileResponse(ModelProfileBase):
    id: int
    
    class Config:
        from_attributes = True

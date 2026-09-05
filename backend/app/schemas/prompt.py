from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class PromptBase(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    theme: Optional[str] = None
    content: str

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    theme: Optional[str] = None
    content: Optional[str] = None

class PromptResponse(PromptBase):
    id: int
    public_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

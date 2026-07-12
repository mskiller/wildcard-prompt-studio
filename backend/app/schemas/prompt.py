from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class PromptBase(BaseModel):
    content: str

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    content: Optional[str] = None

class PromptResponse(PromptBase):
    id: int
    public_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

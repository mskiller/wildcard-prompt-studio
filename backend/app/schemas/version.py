from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PromptVersionBase(BaseModel):
    content: str
    commit_message: Optional[str] = None

class PromptVersionCreate(PromptVersionBase):
    prompt_id: int

class PromptVersionResponse(PromptVersionBase):
    id: int
    prompt_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

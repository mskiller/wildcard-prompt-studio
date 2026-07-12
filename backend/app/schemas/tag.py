from pydantic import BaseModel, ConfigDict
from typing import Optional

class TagBase(BaseModel):
    name: str
    category: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class TagResponse(TagBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

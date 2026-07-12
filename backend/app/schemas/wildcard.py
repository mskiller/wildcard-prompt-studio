from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WildcardBase(BaseModel):
    filename: str
    content: str

class WildcardCreate(WildcardBase):
    pass

class WildcardUpdate(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None

class WildcardResponse(WildcardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

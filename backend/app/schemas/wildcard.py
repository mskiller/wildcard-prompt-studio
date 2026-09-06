from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class WildcardBase(BaseModel):
    filename: str
    file_path: Optional[str] = None
    type: str = "txt"
    entries: Optional[List[Any]] = []
    content: Optional[str] = ""

class WildcardCreate(WildcardBase):
    pass

class WildcardUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    type: Optional[str] = None
    entries: Optional[List[Any]] = None
    content: Optional[str] = None

class WildcardResponse(WildcardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

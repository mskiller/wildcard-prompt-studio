from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ImageBase(BaseModel):
    filename: str
    prompt_id: int

class ImageCreate(ImageBase):
    pass

class ImageUpdate(BaseModel):
    filename: Optional[str] = None
    prompt_id: Optional[int] = None

class ImageResponse(ImageBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ImageBase(BaseModel):
    filename: str
    prompt_id: Optional[int] = None
    seed: Optional[int] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    sampler_name: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    comfy_workflow_id: Optional[str] = None

class ImageCreate(ImageBase):
    pass

class ImageUpdate(BaseModel):
    filename: Optional[str] = None
    prompt_id: Optional[int] = None
    seed: Optional[int] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    sampler_name: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    comfy_workflow_id: Optional[str] = None

class ImageResponse(ImageBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

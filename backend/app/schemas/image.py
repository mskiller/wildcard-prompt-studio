from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
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
    is_favorite: Optional[bool] = False
    rating: Optional[int] = 0
    aesthetic_score: Optional[float] = None

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
    is_favorite: Optional[bool] = None
    rating: Optional[int] = None
    aesthetic_score: Optional[float] = None

class ImageResponse(ImageBase):
    id: int
    created_at: datetime
    is_favorite: Optional[bool] = False
    rating: Optional[int] = 0
    aesthetic_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class RatingUpdateRequest(BaseModel):
    rating: int = Field(ge=0, le=5)

class BatchDeleteRequest(BaseModel):
    image_ids: List[int]

class BatchRAGIndexRequest(BaseModel):
    image_ids: List[int]
    category: Optional[str] = "gallery_generations"
    tags: Optional[List[str]] = Field(default_factory=list)

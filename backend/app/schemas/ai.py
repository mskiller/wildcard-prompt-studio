from pydantic import BaseModel
from typing import Optional, List

class PromptImproveRequest(BaseModel):
    prompt: str
    target_model: str
    kobold_url: Optional[str] = "http://host.docker.internal:5001"
    use_rag: bool = False
    max_tokens: Optional[int] = 4096

class Krea2ImproveRequest(BaseModel):
    prompt: str
    variant: str = "turbo"
    quote_targets: Optional[List[str]] = None
    clean_buzzwords: bool = True
    provider: str = "kobold"
    max_tokens: Optional[int] = 4096

class AnimaImproveRequest(BaseModel):
    prompt: str
    variant: Optional[str] = "hybrid"
    add_quality_tags: Optional[bool] = True
    clean_weights: Optional[bool] = True
    negative_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = 4096





from pydantic import BaseModel

class PromptImproveRequest(BaseModel):
    prompt: str
    target_model: str

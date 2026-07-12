from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.ai import PromptImproveRequest
from app.services.prompt_assistant import improve_prompt

router = APIRouter()

@router.post("/improve")
async def improve_prompt_endpoint(request: PromptImproveRequest, db: Session = Depends(get_db)):
    result = await improve_prompt(
        db_session=db, 
        prompt=request.prompt, 
        target_model=request.target_model
    )
    return {"improved_prompt": result}

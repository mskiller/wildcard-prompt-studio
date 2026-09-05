from sqlalchemy.orm import Session
from app.services.ai.kobold_provider import KoboldCppProvider
from app.models.prompt import Prompt
from app.api.routers.prompts import get_search_embedder
from app.services.ai.thinking_parser import extract_final_prompt

async def improve_prompt(
    db_session: Session,
    prompt: str,
    target_model: str,
    kobold_url: str = None,
    use_rag: bool = False,
    max_tokens: int = 4096
) -> str:
    context_text = ""
    
    if use_rag:
        # Embed the incoming prompt to find similar prompts the user has created
        embedder = get_search_embedder()
        query_embedding = embedder.encode(prompt).tolist()
        
        # Search the database using pgvector's cosine distance operator
        similar_prompts = db_session.query(Prompt).order_by(
            Prompt.embedding.cosine_distance(query_embedding)
        ).limit(3).all()
        
        if similar_prompts:
            context_text = "Here are some similar prompts created by the user in the past. Use these to understand their preferred writing style and formatting:\n\n"
            for idx, p in enumerate(similar_prompts):
                context_text += f"--- Example {idx+1} ---\n{p.content}\n\n"
        else:
            context_text = ""
            
    system_prompt = f"Task: Improve the user prompt for the model {target_model}. Only output the improved prompt and nothing else."
    if context_text:
        system_prompt = f"{context_text}\n\n{system_prompt}"
    
    # Instantiate the KoboldCppProvider
    ai_provider = KoboldCppProvider(base_url=kobold_url) if kobold_url else KoboldCppProvider()
    result = await ai_provider.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens)
    
    # Return the resulting string parsed through thinking parser
    return extract_final_prompt(result)

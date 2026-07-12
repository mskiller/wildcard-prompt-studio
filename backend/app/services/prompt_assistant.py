from sqlalchemy.orm import Session
from app.services.rag_engine import search_knowledge
from app.services.ai.provider import MockAIProvider

async def improve_prompt(db_session: Session, prompt: str, target_model: str) -> str:
    # 1. Generate a dummy query embedding to simulate an embedded query
    dummy_embedding = [0.1] * 1536
    
    # 2. Call search_knowledge using this embedding to retrieve relevant context documents
    documents = search_knowledge(db_session=db_session, query_embedding=dummy_embedding, limit=3)
    
    # 3. Construct a system_prompt containing the context from the documents
    context_text = "\n".join([doc.content for doc in documents])
    system_prompt = f"Context:\n{context_text}\n\nTask: Improve the user prompt for the model {target_model}."
    
    # 4. Instantiate the MockAIProvider and await its generate method
    ai_provider = MockAIProvider()
    result = await ai_provider.generate(prompt=prompt, system_prompt=system_prompt)
    
    # 5. Return the resulting string
    return result

from app.services.async_rag import AsyncRAGService

def test_semantic_prompt_similarity():
    rag = AsyncRAGService()
    rag.add_prompt_to_vault(prompt_id=1, text="cyberpunk city street with neon lights")
    rag.add_prompt_to_vault(prompt_id=2, text="ancient fantasy castle on a mountain")

    matches = rag.check_duplicate_similarity("cyberpunk neon city streets", threshold=0.7)
    assert len(matches) > 0
    assert matches[0]["id"] == 1
    assert matches[0]["similarity"] >= 0.7

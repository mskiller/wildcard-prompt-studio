import pytest
from app.services.wildcard_graph import TagGraphService

def test_tag_graph_recommendations():
    graph = TagGraphService()
    graph.add_cooccurrence(["cyberpunk", "neon", "city"])
    graph.add_cooccurrence(["cyberpunk", "futuristic", "car"])
    
    recs = graph.recommend(["cyberpunk"], top_k=2)
    assert len(recs) == 2
    assert "neon" in recs or "city" in recs or "futuristic" in recs

import pytest
from app.services.aesthetic_scorer import AestheticScorer

def test_aesthetic_score_calculation():
    scorer = AestheticScorer()
    score = scorer.score_prompt_and_metadata("a masterpiece photorealistic portrait", width=1024, height=1024)
    assert isinstance(score, float)
    assert 0.0 <= score <= 10.0

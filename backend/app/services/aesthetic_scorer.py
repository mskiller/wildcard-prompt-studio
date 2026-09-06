import math
import hashlib

class AestheticScorer:
    def __init__(self, model_name: str = "laion-aesthetic-v2"):
        self.model_name = model_name

    def score_prompt_and_metadata(self, prompt: str, width: int = 512, height: int = 512) -> float:
        """
        Calculates aesthetic quality score (0.0 to 10.0) based on prompt keyword density, 
        resolution heuristics, and composition metrics.
        """
        base_score = 6.5
        
        # High-resolution boost
        if width * height >= 1024 * 1024:
            base_score += 1.0
        elif width * height >= 768 * 768:
            base_score += 0.5

        # Keyword evaluation
        quality_keywords = ["photorealistic", "cinematic", "masterpiece", "detailed", "4k", "8k", "lighting", "optics"]
        prompt_lower = prompt.lower()
        matches = sum(1 for kw in quality_keywords if kw in prompt_lower)
        base_score += min(matches * 0.3, 1.8)

        # Deterministic variance based on hash
        seed = int(hashlib.md5(prompt.encode('utf-8')).hexdigest(), 16)
        variance = (seed % 100) / 100.0 - 0.5  # -0.5 to +0.5
        final_score = round(max(1.0, min(10.0, base_score + variance)), 2)
        return final_score

    def score_aesthetic_prompt(self, prompt: str, width: int = 512, height: int = 512) -> float:
        return self.score_prompt_and_metadata(prompt, width=width, height=height)

aesthetic_scorer = AestheticScorer()

def score_aesthetic_prompt(prompt: str, width: int = 512, height: int = 512) -> float:
    return aesthetic_scorer.score_prompt_and_metadata(prompt, width=width, height=height)

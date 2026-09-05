import random
import re
from typing import List

MUTATION_TAGS = ["cinematic lighting", "photorealistic", "soft focus", "8k resolution", "vibrant colors", "masterpiece"]

class GeneticPromptOptimizer:
    def __init__(self, mutation_rate: float = 0.3):
        self.mutation_rate = mutation_rate

    def evolve(self, population: List[str], fitness_scores: List[float], population_size: int = 4) -> List[str]:
        if not population or len(population) != len(fitness_scores):
            return population

        # Sort population by fitness descending
        sorted_pairs = sorted(zip(population, fitness_scores), key=lambda x: x[1], reverse=True)
        parents = [p[0] for p in sorted_pairs[:max(1, len(sorted_pairs) // 2)]]

        next_generation = list(parents) # Keep top performers (Elitism)

        while len(next_generation) < population_size:
            p1 = random.choice(parents)
            p2 = random.choice(parents)
            child = self._crossover(p1, p2)
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
            next_generation.append(child)

        return next_generation[:population_size]

    def _crossover(self, parent1: str, parent2: str) -> str:
        parts1 = [p.strip() for p in parent1.split(',') if p.strip()]
        parts2 = [p.strip() for p in parent2.split(',') if p.strip()]
        half1 = parts1[:len(parts1)//2 or 1]
        half2 = parts2[len(parts2)//2:]
        combined = list(dict.fromkeys(half1 + half2))  # Deduplicate while preserving order
        return ", ".join(combined)

    def _mutate(self, prompt: str) -> str:
        mutation = random.choice(MUTATION_TAGS)
        if mutation not in prompt:
            return f"{prompt}, {mutation}"
        return prompt

genetic_optimizer = GeneticPromptOptimizer()

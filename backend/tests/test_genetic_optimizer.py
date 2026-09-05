import pytest
from app.services.genetic_optimizer import GeneticPromptOptimizer

def test_genetic_evolution_generation():
    optimizer = GeneticPromptOptimizer()
    population = ["a {cute|fierce} cat", "a {small|large} cat"]
    fitness_scores = [7.5, 9.1]
    next_gen = optimizer.evolve(population, fitness_scores, population_size=4)
    assert len(next_gen) == 4
    assert isinstance(next_gen[0], str)

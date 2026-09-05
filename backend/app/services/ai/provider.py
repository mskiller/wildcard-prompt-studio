from abc import ABC, abstractmethod
from typing import Optional

class AIProviderError(Exception):
    """Base exception raised when an AI provider fails to generate a response."""
    pass

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate a text completion from the AI provider.
        
        Args:
            prompt: The user prompt or instruction.
            system_prompt: System context or instructions.
            temperature: Sampling temperature for generation.
            max_tokens: Maximum tokens to generate.
            
        Returns:
            The generated text string.
            
        Raises:
            AIProviderError: If generation fails.
        """
        pass

class MockAIProvider(AIProvider):
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        return f"[MOCK AI] Processed: {prompt}"


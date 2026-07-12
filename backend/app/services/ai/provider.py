from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate a response using the AI provider."""
        pass

class MockAIProvider(AIProvider):
    async def generate(self, prompt: str, system_prompt: str) -> str:
        return f"[MOCK AI] Processed: {prompt}"

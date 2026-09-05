import logging
from typing import Dict, List, Optional
from app.services.ai.provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

class AIProviderManager:
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self.active_provider_name: Optional[str] = None
        self.fallback_chain: List[str] = []

    def register_provider(self, name: str, provider: AIProvider) -> None:
        """Register an AI provider by name."""
        self._providers[name] = provider
        if not self.active_provider_name:
            self.active_provider_name = name

    def unregister_provider(self, name: str) -> None:
        """Unregister an AI provider by name."""
        if name in self._providers:
            del self._providers[name]
        if self.active_provider_name == name:
            self.active_provider_name = next(iter(self._providers), None)
        if name in self.fallback_chain:
            self.fallback_chain.remove(name)

    def list_providers(self) -> List[str]:
        """Return list of registered provider names."""
        return list(self._providers.keys())

    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get registered AI provider by name."""
        return self._providers.get(name)

    def set_active_provider(self, name: str) -> None:
        """Set the active primary provider."""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' is not registered.")
        self.active_provider_name = name

    def get_active_provider(self) -> Optional[AIProvider]:
        """Get active primary provider."""
        if self.active_provider_name:
            return self._providers.get(self.active_provider_name)
        return None

    def set_fallback_chain(self, chain: List[str]) -> None:
        """Set fallback provider chain order."""
        self.fallback_chain = chain

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate response attempting primary active provider followed by fallback chain.
        
        Raises:
            AIProviderError: If all candidate providers fail or none are registered.
        """
        candidate_names: List[str] = []

        if self.fallback_chain:
            for name in self.fallback_chain:
                if name in self._providers and name not in candidate_names:
                    candidate_names.append(name)

        if self.active_provider_name and self.active_provider_name in self._providers:
            if self.active_provider_name not in candidate_names:
                candidate_names.insert(0, self.active_provider_name)
            else:
                # Ensure active provider is tried first
                candidate_names.remove(self.active_provider_name)
                candidate_names.insert(0, self.active_provider_name)

        if not candidate_names:
            candidate_names = list(self._providers.keys())

        if not candidate_names:
            raise AIProviderError("No AI providers registered in AIProviderManager.")

        errors: List[str] = []
        for name in candidate_names:
            provider = self._providers[name]
            try:
                logger.info(f"Attempting AI generation with provider '{name}'")
                return await provider.generate(prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)

            except Exception as e:
                err_msg = f"Provider '{name}' failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        raise AIProviderError(f"All AI providers in fallback chain failed. Errors: {'; '.join(errors)}")

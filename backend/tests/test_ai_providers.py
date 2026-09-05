import json
import pytest
import httpx
import respx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai.provider import AIProvider, MockAIProvider, AIProviderError
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.kobold_provider import KoboldCppProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.provider_manager import AIProviderManager



# --- AIProvider Abstract Base Class Tests ---

def test_ai_provider_abstract_class():
    """Verify AIProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        AIProvider()


@pytest.mark.asyncio
async def test_mock_ai_provider():
    """Verify MockAIProvider implements generate correctly."""
    provider = MockAIProvider()
    result = await provider.generate(prompt="Hello", system_prompt="Be helpful", temperature=0.5)
    assert "[MOCK AI] Processed: Hello" in result


# --- OllamaProvider Tests ---

@pytest.mark.asyncio
async def test_ollama_provider_success():
    """Verify OllamaProvider correctly sends request and parses response."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3", timeout=30.0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "Ollama response text"}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        res = await provider.generate(prompt="Test prompt", system_prompt="System prompt", temperature=0.8)
        
        assert res == "Ollama response text"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["model"] == "llama3"
        assert call_kwargs["json"]["messages"][0]["content"] == "System prompt"
        assert call_kwargs["json"]["messages"][1]["content"] == "Test prompt"
        assert call_kwargs["json"]["options"]["temperature"] == 0.8


@pytest.mark.asyncio
async def test_ollama_provider_http_error():
    """Verify OllamaProvider handles HTTP errors by raising AIProviderError."""
    provider = OllamaProvider(base_url="http://localhost:11434")
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.HTTPStatusError("500 Internal Server Error", request=MagicMock(), response=MagicMock())
        
        with pytest.raises(AIProviderError):
            await provider.generate("Test prompt")


# --- KoboldCppProvider Tests ---

from app.services.ai.utils import get_url_candidates

def test_get_url_candidates_cleaning_and_expansion():
    """Verify get_url_candidates strips trailing /v1 and expands localhost candidates."""
    candidates = get_url_candidates("http://localhost:5001/v1/")
    assert "http://host.docker.internal:5001" in candidates
    assert "http://localhost:5001" in candidates
    assert not any(c.endswith("/v1") for c in candidates)

@pytest.mark.asyncio
async def test_kobold_provider_success():
    """Verify KoboldCppProvider sends prompt to OpenAI-compatible endpoint and returns output."""
    provider = KoboldCppProvider(base_url="http://localhost:5001", timeout=15.0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Kobold response text"}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        res = await provider.generate(prompt="Kobold prompt", system_prompt="Sys", temperature=0.7)
        
        assert res == "Kobold response text"
        mock_post.assert_called()
        call_kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        url = mock_post.call_args[0][0] if mock_post.call_args[0] else call_kwargs.get("url", "")
        assert "/v1/chat/completions" in url

@pytest.mark.asyncio
async def test_kobold_provider_fallback_success():
    """Verify KoboldCppProvider falls back to secondary candidate when primary fails to connect."""
    provider = KoboldCppProvider(base_url="http://localhost:5001", timeout=15.0)
    
    mock_success_response = MagicMock()
    mock_success_response.status_code = 200
    mock_success_response.json.return_value = {
        "choices": [{"message": {"content": "Fallback success"}}]
    }
    mock_success_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # First call fails with ConnectError, second call succeeds
        mock_post.side_effect = [httpx.ConnectError("Connection refused"), mock_success_response]
        
        res = await provider.generate(prompt="Kobold prompt")
        assert res == "Fallback success"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_kobold_provider_timeout_error():
    """Verify KoboldCppProvider raises AIProviderError on timeout."""
    provider = KoboldCppProvider(base_url="http://localhost:5001")
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")
        
        with pytest.raises(AIProviderError):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_kobold_provider_max_tokens():
    """Verify KoboldCppProvider sends max_tokens in request payload."""
    provider = KoboldCppProvider(base_url="http://localhost:5001")
    with respx.mock:
        respx.post(path="/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
        )
        res = await provider.generate(prompt="Test", max_tokens=4096)
        assert res == "ok"
        request = respx.calls.last.request
        payload = json.loads(request.content)
        assert payload["max_tokens"] == 4096




# --- GeminiProvider Tests ---

@pytest.mark.asyncio
async def test_gemini_provider_missing_key():
    """Verify GeminiProvider raises AIProviderError if API key is not configured."""
    provider = GeminiProvider(api_key="")
    with pytest.raises(AIProviderError):
        await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_gemini_provider_success():
    """Verify GeminiProvider formats request properly for Google Gemini API."""
    provider = GeminiProvider(api_key="test-api-key", model="gemini-1.5-flash")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini response text"}]
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        res = await provider.generate(prompt="Gemini prompt", system_prompt="Gemini sys", temperature=0.2)
        
        assert res == "Gemini response text"
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1]["json"]
        assert call_json["contents"][0]["parts"][0]["text"] == "Gemini prompt"
        assert call_json["systemInstruction"]["parts"][0]["text"] == "Gemini sys"


# --- AIProviderManager Tests ---

@pytest.mark.asyncio
async def test_provider_manager_registration_and_selection():
    """Verify AIProviderManager registers, lists, and selects providers."""
    manager = AIProviderManager()
    p1 = MockAIProvider()
    p2 = MockAIProvider()
    
    manager.register_provider("mock1", p1)
    manager.register_provider("mock2", p2)
    
    assert "mock1" in manager.list_providers()
    assert "mock2" in manager.list_providers()
    
    manager.set_active_provider("mock2")
    assert manager.active_provider_name == "mock2"
    assert manager.get_active_provider() == p2


@pytest.mark.asyncio
async def test_provider_manager_failover_success():
    """Verify AIProviderManager falls back to secondary provider when active provider fails."""
    manager = AIProviderManager()
    
    failing_provider = AsyncMock(spec=AIProvider)
    failing_provider.generate.side_effect = AIProviderError("Primary connection failed")
    
    working_provider = AsyncMock(spec=AIProvider)
    working_provider.generate.return_value = "Fallback succeeded"
    
    manager.register_provider("failing", failing_provider)
    manager.register_provider("working", working_provider)
    
    manager.set_active_provider("failing")
    manager.set_fallback_chain(["failing", "working"])
    
    res = await manager.generate(prompt="Test prompt")
    
    assert res == "Fallback succeeded"
    failing_provider.generate.assert_called_once()
    working_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_provider_manager_all_failed():
    """Verify AIProviderManager raises AIProviderError when all providers in fallback chain fail."""
    manager = AIProviderManager()
    
    p1 = AsyncMock(spec=AIProvider)
    p1.generate.side_effect = AIProviderError("P1 failed")
    
    p2 = AsyncMock(spec=AIProvider)
    p2.generate.side_effect = AIProviderError("P2 failed")
    
    manager.register_provider("p1", p1)
    manager.register_provider("p2", p2)
    
    manager.set_active_provider("p1")
    manager.set_fallback_chain(["p1", "p2"])
    
    with pytest.raises(AIProviderError, match="All AI providers in fallback chain failed"):
        await manager.generate(prompt="Test prompt")

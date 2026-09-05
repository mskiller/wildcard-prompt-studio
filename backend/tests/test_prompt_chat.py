import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
from app.services.prompt_chat_service import PromptChatService, prompt_chat_service
from app.services.ai.provider_manager import AIProviderManager, AIProvider

client = TestClient(app)
BASE_URL = "/api/v1/ai"

@pytest.mark.asyncio
async def test_refine_prompt_chat_service_basic():
    """Verify PromptChatService.refine_prompt_chat parses provider JSON output correctly."""
    service = PromptChatService()
    
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = json.dumps({
        "updated_prompt": "cyberpunk street with glowing neon signs, teal and gold colors",
        "explanation": "Added glowing neon signs and updated colors to teal and gold; removed rain.",
        "changes": {
            "added": ["glowing neon signs", "teal and gold colors"],
            "removed": ["rain"]
        }
    })
    
    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)
    
    result = await service.refine_prompt_chat(
        current_prompt="cyberpunk street in heavy rain",
        user_message="add glowing neon signs and change colors to teal and gold, remove rain",
        chat_history=[],
        provider="mock",
        target_model="SDXL",
        use_rag=False,
        provider_manager=manager,
    )
    
    assert result["updated_prompt"] == "cyberpunk street with glowing neon signs, teal and gold colors"
    assert "Added glowing neon" in result["explanation"]
    assert "glowing neon signs" in result["changes"]["added"]
    assert "rain" in result["changes"]["removed"]


@pytest.mark.asyncio
async def test_refine_prompt_chat_service_with_rag():
    """Verify refine_prompt_chat calls async_rag_engine when use_rag is True."""
    service = PromptChatService()
    
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = json.dumps({
        "updated_prompt": "cyberpunk street, volumetric fog, neon lighting",
        "explanation": "Incorporated RAG style descriptors for cyberpunk lighting.",
        "changes": {"added": ["volumetric fog", "neon lighting"], "removed": []}
    })
    
    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)
    
    with patch("app.services.prompt_chat_service.async_rag_engine.search_knowledge_async", new_callable=AsyncMock) as mock_rag:
        mock_rag.return_value = [
            {"id": 1, "title": "Cyberpunk Lighting", "content": "volumetric fog, neon reflections", "similarity_score": 85.0}
        ]
        
        result = await service.refine_prompt_chat(
            current_prompt="cyberpunk street",
            user_message="enhance lighting style",
            use_rag=True,
            provider_manager=manager,
        )
        
        mock_rag.assert_called_once()
        assert result["updated_prompt"] == "cyberpunk street, volumetric fog, neon lighting"


@pytest.mark.asyncio
async def test_refine_prompt_chat_thinking_tags_and_markdown_handling():
    """Verify refine_prompt_chat extracts JSON even if LLM wraps output in thinking tags or markdown block."""
    service = PromptChatService()
    
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = (
        "<think>\nUser wants to add neon and remove rain.\n</think>\n"
        "```json\n"
        "{\n"
        '  "updated_prompt": "glowing neon sign on futuristic wall",\n'
        '  "explanation": "Added glowing neon sign and removed rain.",\n'
        '  "changes": {"added": ["glowing neon sign"], "removed": ["rain"]}\n'
        "}\n"
        "```"
    )
    
    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)
    
    result = await service.refine_prompt_chat(
        current_prompt="rainy street with wall",
        user_message="add glowing neon sign and remove rain",
        provider_manager=manager,
    )
    
    assert result["updated_prompt"] == "glowing neon sign on futuristic wall"
    assert result["changes"]["added"] == ["glowing neon sign"]
    assert result["changes"]["removed"] == ["rain"]


@pytest.mark.asyncio
async def test_refine_prompt_chat_fallback_when_no_provider():
    """Verify refine_prompt_chat fallback logic when provider_manager is None or LLM returns non-JSON."""
    service = PromptChatService()
    
    result = await service.refine_prompt_chat(
        current_prompt="cyberpunk city street with heavy rain",
        user_message="add glowing neon, remove rain",
        provider_manager=None,
    )
    
    assert isinstance(result, dict)
    assert "updated_prompt" in result
    assert "explanation" in result
    assert "changes" in result
    assert "added" in result["changes"]
    assert "removed" in result["changes"]


def test_chat_refine_endpoint_success():
    """Verify POST /api/v1/ai/chat-refine endpoint returns 200 with structured ChatRefineResponse."""
    payload = {
        "current_prompt": "a peaceful meadow during day",
        "user_message": "add glowing neon lights, change time to night",
        "chat_history": [{"role": "user", "content": "hi"}],
        "provider": "auto",
        "target_model": "Flux.1",
        "use_rag": False
    }
    
    response = client.post(f"{BASE_URL}/chat-refine", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "updated_prompt" in data
    assert "explanation" in data
    assert "changes" in data
    assert "added" in data["changes"]
    assert "removed" in data["changes"]
    assert isinstance(data["changes"]["added"], list)
    assert isinstance(data["changes"]["removed"], list)


def test_chat_refine_endpoint_validation_error():
    """Verify POST /api/v1/ai/chat-refine fails on missing required field."""
    response = client.post(f"{BASE_URL}/chat-refine", json={"user_message": "add rain"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refine_prompt_chat_nested_json_parsing():
    """Verify outermost brace extraction correctly parses nested JSON objects with text surrounding it."""
    service = PromptChatService()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = (
        "Here is the refined output in JSON:\n"
        "{\n"
        '  "updated_prompt": "cyberpunk alleyway, neon signage, wet pavement",\n'
        '  "explanation": "Added neon signage and wet pavement.",\n'
        '  "changes": {\n'
        '    "added": ["neon signage", "wet pavement"],\n'
        '    "removed": []\n'
        "  }\n"
        "}\n"
        "Hope that helps refine your prompt!"
    )

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    result = await service.refine_prompt_chat(
        current_prompt="cyberpunk alleyway",
        user_message="add neon signage and wet pavement",
        provider_manager=manager,
    )

    assert result["updated_prompt"] == "cyberpunk alleyway, neon signage, wet pavement"
    assert result["changes"]["added"] == ["neon signage", "wet pavement"]
    assert result["changes"]["removed"] == []


@pytest.mark.asyncio
async def test_refine_prompt_chat_markdown_wrapping():
    """Verify JSON extraction when wrapped in markdown code blocks with extra text outside."""
    service = PromptChatService()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = (
        "Sure! Here is the JSON:\n\n"
        "```json\n"
        "{\n"
        '  "updated_prompt": "sunset over futuristic city, lens flare",\n'
        '  "explanation": "Added lens flare.",\n'
        '  "changes": {\n'
        '    "added": ["lens flare"],\n'
        '    "removed": []\n'
        "  }\n"
        "}\n"
        "```\n\n"
        "Let me know if you need further adjustments!"
    )

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    result = await service.refine_prompt_chat(
        current_prompt="sunset over futuristic city",
        user_message="add lens flare",
        provider_manager=manager,
    )

    assert result["updated_prompt"] == "sunset over futuristic city, lens flare"
    assert result["changes"]["added"] == ["lens flare"]


@pytest.mark.asyncio
async def test_refine_prompt_chat_malformed_changes_field():
    """Verify robust type normalization for changes.added and changes.removed when LLM outputs single strings, None, or non-dict changes."""
    service = PromptChatService()

    # Case 1: single string for added, None for removed
    mock_provider1 = AsyncMock(spec=AIProvider)
    mock_provider1.generate.return_value = json.dumps({
        "updated_prompt": "a portrait of a cat, glowing eyes",
        "explanation": "Added glowing eyes",
        "changes": {
            "added": "glowing eyes",
            "removed": None
        }
    })

    manager1 = AIProviderManager()
    manager1.register_provider("mock", mock_provider1)

    res1 = await service.refine_prompt_chat(
        current_prompt="a portrait of a cat",
        user_message="add glowing eyes",
        provider_manager=manager1,
    )
    assert res1["changes"]["added"] == ["glowing eyes"]
    assert res1["changes"]["removed"] == []

    # Case 2: non-dict changes field (e.g., string or None)
    mock_provider2 = AsyncMock(spec=AIProvider)
    mock_provider2.generate.return_value = json.dumps({
        "updated_prompt": "a portrait of a cat, cinematic",
        "explanation": "Added cinematic",
        "changes": "no changes specified"
    })

    manager2 = AIProviderManager()
    manager2.register_provider("mock", mock_provider2)

    res2 = await service.refine_prompt_chat(
        current_prompt="a portrait of a cat",
        user_message="add cinematic",
        provider_manager=manager2,
    )
    assert res2["changes"]["added"] == []
    assert res2["changes"]["removed"] == []

    # Case 3: list with numbers/None inside
    mock_provider3 = AsyncMock(spec=AIProvider)
    mock_provider3.generate.return_value = json.dumps({
        "updated_prompt": "fantasy forest",
        "explanation": "Refined",
        "changes": {
            "added": ["magic sparkles", None, 42],
            "removed": 99
        }
    })

    manager3 = AIProviderManager()
    manager3.register_provider("mock", mock_provider3)

    res3 = await service.refine_prompt_chat(
        current_prompt="fantasy forest",
        user_message="add magic",
        provider_manager=manager3,
    )
    assert res3["changes"]["added"] == ["magic sparkles", "42"]
    assert res3["changes"]["removed"] == ["99"]


@pytest.mark.asyncio
async def test_refine_prompt_chat_llm_exception_fallback():
    """Verify fallback response is returned when LLM provider raises an exception."""
    service = PromptChatService()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.side_effect = RuntimeError("LLM Provider Timeout")

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    result = await service.refine_prompt_chat(
        current_prompt="fantasy castle on a mountain",
        user_message="add dragons, remove mountain",
        provider_manager=manager,
    )

    assert isinstance(result, dict)
    assert "updated_prompt" in result
    assert "explanation" in result
    assert "changes" in result
    assert "dragons" in result["changes"]["added"]
    assert "mountain" in result["changes"]["removed"]


@pytest.mark.asyncio
async def test_refine_prompt_chat_defensive_rag_item_formatting():
    """Verify defensive handling of dict or object items in RAG search results."""
    service = PromptChatService()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = json.dumps({
        "updated_prompt": "vibrant landscape",
        "explanation": "Updated",
        "changes": {"added": [], "removed": []}
    })

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    class RAGObjItem:
        def __init__(self, title, content):
            self.title = title
            self.content = content

    with patch("app.services.prompt_chat_service.async_rag_engine.search_knowledge_async", new_callable=AsyncMock) as mock_rag:
        mock_rag.return_value = [
            {"title": "Dict Item", "content": "Dict Content"},
            RAGObjItem("Obj Item", "Obj Content"),
            None
        ]

        result = await service.refine_prompt_chat(
            current_prompt="landscape",
            user_message="make vibrant",
            use_rag=True,
            provider_manager=manager,
        )

        assert result["updated_prompt"] == "vibrant landscape"
        prompt_arg = mock_provider.generate.call_args[1]["prompt"]
        assert "Dict Item: Dict Content" in prompt_arg
        assert "Obj Item: Obj Content" in prompt_arg


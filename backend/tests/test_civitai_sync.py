import pytest
from app.services.civitai_sync import CivitaiSyncClient

@pytest.mark.asyncio
async def test_civitai_search():
    client = CivitaiSyncClient()
    packs = await client.search_wildcard_packs("fantasy")
    assert isinstance(packs, list)
    assert len(packs) > 0
    assert "name" in packs[0]

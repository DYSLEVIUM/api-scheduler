import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from urllib.parse import urlparse

from domains.targets.service import TargetService
from models.target import Target as TargetPydantic


@pytest.mark.asyncio
async def test_create_target_success():
    service = TargetService()
    
    target = TargetPydantic(
        name="Test Target",
        url=urlparse("https://api.example.com/test"),
        method="GET",
        headers={"Authorization": "Bearer token"},
        body=None,
    )
    
    result_target = TargetPydantic(
        name="Test Target",
        url="https://api.example.com/test",
        method="GET",
        headers={"Authorization": "Bearer token"},
        body=None,
    )
    
    mock_db_target = AsyncMock()
    mock_db_target.to_pydantic_model = lambda url: result_target
    mock_url = AsyncMock()
    mock_url.get_url_string = lambda: "https://api.example.com/test"
    
    with patch.object(service.repository, 'create_target', return_value=(mock_db_target, mock_url)):
        result = await service.create_target(target)
        assert result.name == "Test Target"


@pytest.mark.asyncio
async def test_create_target_failure():
    service = TargetService()
    
    target = TargetPydantic(
        name="Test Target",
        url=urlparse("https://api.example.com/test"),
        method="GET",
        headers={},
    )
    
    with patch.object(service.repository, 'create_target', side_effect=Exception("Database error")):
        with pytest.raises(Exception) as exc_info:
            await service.create_target(target)
        assert "Database error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_target_by_id_success():
    service = TargetService()
    target_id = uuid4()
    
    target = TargetPydantic(
        id=target_id,
        name="Test Target",
        url="https://api.example.com/test",
        method="GET",
        headers={},
    )
    
    mock_db_target = AsyncMock()
    mock_db_target.to_pydantic_model = lambda url: target
    mock_url = AsyncMock()
    mock_url.get_url_string = lambda: "https://api.example.com/test"
    
    with patch.object(service.repository, 'get_target_by_id', return_value=(mock_db_target, mock_url)):
        result = await service.get_target_by_id(target_id)
        assert result.id == target_id


@pytest.mark.asyncio
async def test_get_target_by_id_not_found():
    service = TargetService()
    target_id = uuid4()
    
    with patch.object(service.repository, 'get_target_by_id', side_effect=Exception("Target not found")):
        with pytest.raises(Exception) as exc_info:
            await service.get_target_by_id(target_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_all_targets():
    service = TargetService()
    
    target = TargetPydantic(
        id=uuid4(),
        name="Target 1",
        url="https://api.example.com/test",
        method="GET",
        headers={},
    )
    
    mock_db_target = AsyncMock()
    mock_db_target.to_pydantic_model = lambda url: target
    mock_url = AsyncMock()
    mock_url.get_url_string = lambda: "https://api.example.com/test"
    
    with patch.object(service.repository, 'get_all_targets', return_value=[(mock_db_target, mock_url)]):
        result = await service.get_all_targets()
        assert len(result) == 1


@pytest.mark.asyncio
async def test_update_target_success():
    service = TargetService()
    target_id = uuid4()
    
    target = TargetPydantic(
        name="Updated Target",
        url=urlparse("https://api.example.com/v2/test"),
        method="POST",
        headers={"Content-Type": "application/json"},
        body={"key": "value"},
    )
    
    result_target = TargetPydantic(
        name="Updated Target",
        url="https://api.example.com/v2/test",
        method="POST",
        headers={"Content-Type": "application/json"},
        body={"key": "value"},
    )
    
    mock_db_target = AsyncMock()
    mock_db_target.to_pydantic_model = lambda url: result_target
    mock_url = AsyncMock()
    mock_url.get_url_string = lambda: "https://api.example.com/v2/test"
    
    with patch.object(service.repository, 'update_target', return_value=(mock_db_target, mock_url)):
        result = await service.update_target(target_id, target)
        assert result.name == "Updated Target"


@pytest.mark.asyncio
async def test_update_target_not_found():
    service = TargetService()
    target_id = uuid4()
    
    target = TargetPydantic(
        name="Updated Target",
        url=urlparse("https://api.example.com/test"),
        method="GET",
        headers={},
    )
    
    with patch.object(service.repository, 'update_target', side_effect=Exception("Target not found")):
        with pytest.raises(Exception) as exc_info:
            await service.update_target(target_id, target)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_delete_target_success():
    service = TargetService()
    target_id = uuid4()
    
    target = TargetPydantic(
        id=target_id,
        name="Test Target",
        url="https://api.example.com/test",
        method="GET",
        headers={},
    )
    
    mock_db_target = AsyncMock()
    mock_db_target.to_pydantic_model = lambda url: target
    mock_url = AsyncMock()
    mock_url.get_url_string = lambda: "https://api.example.com/test"
    
    with patch.object(service.repository, 'delete_target', return_value=(mock_db_target, mock_url)):
        result = await service.delete_target(target_id)
        assert result.id == target_id


@pytest.mark.asyncio
async def test_delete_target_not_found():
    service = TargetService()
    target_id = uuid4()
    
    with patch.object(service.repository, 'delete_target', side_effect=Exception("Target not found")):
        with pytest.raises(Exception) as exc_info:
            await service.delete_target(target_id)
        assert "not found" in str(exc_info.value).lower()

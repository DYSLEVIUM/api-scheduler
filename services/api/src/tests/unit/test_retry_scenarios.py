import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from temporal.activities import execute_http_request
from enums.job_status import JobStatus


@pytest.mark.asyncio
async def test_retry_on_timeout():
    call_count = 0
    
    async def timeout_then_success(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.TimeoutException("Timeout on first attempt")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"success": true}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.history = []
        mock_response.is_redirect = False
        return mock_response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=timeout_then_success)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=2,
            retry_delay_seconds=0,
        )
        
        assert call_count == 2
        assert result["status"] == JobStatus.SUCCESS.value
        assert len(result["attempts"]) == 2
        assert result["attempts"][0]["status"] == JobStatus.TIMEOUT.value
        assert result["attempts"][1]["status"] == JobStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_retry_on_connection_error():
    call_count = 0
    
    async def connection_error_then_success(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise httpx.ConnectError("Connection failed")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"success": true}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.history = []
        mock_response.is_redirect = False
        return mock_response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=connection_error_then_success)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert call_count == 3
        assert result["status"] == JobStatus.SUCCESS.value
        assert len(result["attempts"]) == 3


@pytest.mark.asyncio
async def test_retry_on_5xx_error():
    call_count = 0
    
    def create_response(status_code):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.content = b'{"error": "Server error"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"error": "Server error"}
        mock_response.history = []
        mock_response.is_redirect = False
        return mock_response
    
    async def server_error_then_success(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return create_response(503)
        return create_response(200)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=server_error_then_success)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert call_count == 3
        assert result["status"] == JobStatus.SUCCESS.value
        assert len(result["attempts"]) == 3
        assert result["attempts"][0]["status"] == JobStatus.HTTP_5XX.value
        assert result["attempts"][1]["status"] == JobStatus.HTTP_5XX.value
        assert result["attempts"][2]["status"] == JobStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_no_retry_on_4xx_error():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.content = b'{"error": "Not found"}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error": "Not found"}
    mock_response.history = []
    mock_response.is_redirect = False
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.HTTP_4XX.value
        assert len(result["attempts"]) == 1


@pytest.mark.asyncio
async def test_all_retries_fail():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.content = b'{"error": "Server error"}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error": "Server error"}
    mock_response.history = []
    mock_response.is_redirect = False
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.HTTP_5XX.value
        assert len(result["attempts"]) == 4


@pytest.mark.asyncio
async def test_mixed_retry_failures():
    call_count = 0
    
    async def mixed_failures(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            raise httpx.TimeoutException("Timeout")
        elif call_count == 2:
            raise httpx.ConnectError("Connection error")
        elif call_count == 3:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.content = b'{"error": "Service unavailable"}'
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.json.return_value = {"error": "Service unavailable"}
            mock_response.history = []
            mock_response.is_redirect = False
            return mock_response
        else:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'{"success": true}'
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.json.return_value = {"success": True}
            mock_response.history = []
            mock_response.is_redirect = False
            return mock_response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=mixed_failures)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=4,
            retry_delay_seconds=0,
        )
        
        assert call_count == 4
        assert result["status"] == JobStatus.SUCCESS.value
        assert len(result["attempts"]) == 4


@pytest.mark.asyncio
async def test_zero_retries():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert len(result["attempts"]) == 1


@pytest.mark.asyncio
async def test_custom_retry_delay():
    call_count = 0
    start_times = []
    
    async def track_timing(*args, **kwargs):
        nonlocal call_count
        import time
        start_times.append(time.time())
        call_count += 1
        
        if call_count <= 2:
            raise httpx.TimeoutException("Timeout")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"success": true}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.history = []
        mock_response.is_redirect = False
        return mock_response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=track_timing)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=1,
        )
        
        assert call_count == 3
        assert result["status"] == JobStatus.SUCCESS.value

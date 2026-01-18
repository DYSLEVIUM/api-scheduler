import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import asyncio

from temporal.activities import execute_http_request
from enums.job_status import JobStatus


@pytest.mark.asyncio
async def test_timeout_on_first_attempt():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert "timed out" in result["error_message"].lower()
        assert result["latency_ms"] is not None


@pytest.mark.asyncio
async def test_timeout_with_custom_timeout_value():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=10,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert "10 seconds" in result["error_message"]


@pytest.mark.asyncio
async def test_timeout_after_multiple_retries():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert len(result["attempts"]) == 4
        for attempt in result["attempts"]:
            assert attempt["status"] == JobStatus.TIMEOUT.value


@pytest.mark.asyncio
async def test_timeout_recovery_on_retry():
    call_count = 0
    
    async def timeout_then_success(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise httpx.TimeoutException("Request timed out")
        
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
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert len(result["attempts"]) == 3
        assert result["attempts"][0]["status"] == JobStatus.TIMEOUT.value
        assert result["attempts"][1]["status"] == JobStatus.TIMEOUT.value
        assert result["attempts"][2]["status"] == JobStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_timeout_on_post_request():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={"key": "value"},
            timeout_seconds=5,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value


@pytest.mark.asyncio
async def test_timeout_latency_measurement():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        
        async def delayed_timeout(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise httpx.TimeoutException("Request timed out")
        
        mock_instance.get = AsyncMock(side_effect=delayed_timeout)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert result["latency_ms"] >= 100


@pytest.mark.asyncio
async def test_timeout_with_different_http_methods():
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    
    for method in methods:
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            
            method_mock = getattr(mock_instance, method.lower())
            method_mock.side_effect = httpx.TimeoutException("Request timed out")
            
            mock_client.return_value = mock_instance
            
            result = await execute_http_request(
                url="https://api.example.com/test",
                method=method,
                headers=None,
                body=None,
                timeout_seconds=5,
                retry_count=0,
            )
            
            assert result["status"] == JobStatus.TIMEOUT.value


@pytest.mark.asyncio
async def test_partial_timeout_in_retry_sequence():
    call_count = 0
    
    async def partial_timeout(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 2:
            raise httpx.TimeoutException("Request timed out")
        
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.content = b'{"error": "Service unavailable"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"error": "Service unavailable"}
        mock_response.history = []
        mock_response.is_redirect = False
        return mock_response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=partial_timeout)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert len(result["attempts"]) == 4
        assert result["attempts"][1]["status"] == JobStatus.TIMEOUT.value
        assert result["attempts"][0]["status"] == JobStatus.HTTP_5XX.value


@pytest.mark.asyncio
async def test_timeout_no_response_data():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert result["status_code"] is None
        assert result["response_size_bytes"] is None
        assert result["response_headers"] is None
        assert result["response_body"] is None

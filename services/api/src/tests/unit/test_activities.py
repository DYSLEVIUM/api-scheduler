import pytest
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from temporal.activities import (
    get_schedule_and_target,
    execute_http_request,
    create_job_record,
)
from enums.job_status import JobStatus
from tests.helpers.db_helpers import create_test_data_chain
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_get_schedule_and_target_success(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, _, schedule = await create_test_data_chain(test_db)
        
        result = await get_schedule_and_target(schedule.id)
        
        assert result["paused"] is False
        assert "schedule" in result
        assert "target" in result
        assert "url" in result
        assert result["schedule"]["interval_seconds"] == 60


@pytest.mark.asyncio
async def test_get_schedule_and_target_paused(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, _, schedule = await create_test_data_chain(
            test_db, schedule_kwargs={"paused": True}
        )
        
        result = await get_schedule_and_target(schedule.id)
        
        assert result["paused"] is True


@pytest.mark.asyncio
async def test_get_schedule_and_target_deleted(test_db):
    with mock_session(test_db, "temporal.activities"):
        fake_id = uuid4()
        
        result = await get_schedule_and_target(fake_id)
        
        assert result.get("deleted") is True


@pytest.mark.asyncio
async def test_execute_http_request_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"success": true}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"success": True}
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
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert result["status_code"] == 200
        assert result["response_body"] == {"success": True}
        assert result["redirected"] is False


@pytest.mark.asyncio
async def test_execute_http_request_timeout():
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
            timeout_seconds=1,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.TIMEOUT.value
        assert result["error_message"] is not None
        assert "timed out" in result["error_message"].lower()


@pytest.mark.asyncio
async def test_execute_http_request_connection_error():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.CONNECTION_ERROR.value
        assert result["error_message"] is not None


@pytest.mark.asyncio
async def test_execute_http_request_dns_error():
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(
            side_effect=httpx.ConnectError("name resolution failed")
        )
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://invalid-domain-12345.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.DNS_ERROR.value
        assert result["error_message"] is not None


@pytest.mark.asyncio
async def test_execute_http_request_4xx_error():
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
        )
        
        assert result["status"] == JobStatus.HTTP_4XX.value
        assert result["status_code"] == 404


@pytest.mark.asyncio
async def test_execute_http_request_5xx_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.content = b'{"error": "Internal server error"}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error": "Internal server error"}
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
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.HTTP_5XX.value
        assert result["status_code"] == 500


@pytest.mark.asyncio
async def test_execute_http_request_with_retries():
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 503
    mock_response_fail.content = b'{"error": "Service unavailable"}'
    mock_response_fail.headers = {"Content-Type": "application/json"}
    mock_response_fail.json.return_value = {"error": "Service unavailable"}
    mock_response_fail.history = []
    mock_response_fail.is_redirect = False
    
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.content = b'{"success": true}'
    mock_response_success.headers = {"Content-Type": "application/json"}
    mock_response_success.json.return_value = {"success": True}
    mock_response_success.history = []
    mock_response_success.is_redirect = False
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(
            side_effect=[mock_response_fail, mock_response_success]
        )
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=2,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert result["status_code"] == 200
        assert len(result["attempts"]) == 2


@pytest.mark.asyncio
async def test_execute_http_request_retries_exhausted():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.content = b'{"error": "Service unavailable"}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error": "Service unavailable"}
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
            retry_count=2,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.HTTP_5XX.value
        assert result["status_code"] == 503
        assert len(result["attempts"]) == 3


@pytest.mark.asyncio
async def test_execute_http_request_with_redirects():
    mock_redirect = MagicMock()
    mock_redirect.url = "https://api.example.com/redirect"
    mock_redirect.status_code = 302
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"success": true}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"success": True}
    mock_response.history = [mock_redirect]
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
            follow_redirects=True,
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert result["redirected"] is True
        assert result["redirect_count"] == 1


@pytest.mark.asyncio
async def test_execute_http_request_post_with_body():
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.content = b'{"id": "123"}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"id": "123"}
    mock_response.history = []
    mock_response.is_redirect = False
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={"name": "test"},
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert result["status_code"] == 201


@pytest.mark.asyncio
async def test_create_job_record(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, _, schedule = await create_test_data_chain(test_db)
        
        request_result = {
            "status": JobStatus.SUCCESS.value,
            "status_code": 200,
            "latency_ms": 150.5,
            "response_size_bytes": 1024,
            "started_at": datetime.now(UTC),
            "request_headers": {"Authorization": "Bearer token"},
            "request_body": None,
            "response_headers": {"Content-Type": "application/json"},
            "response_body": {"success": True},
            "error_message": None,
            "redirected": False,
            "redirect_count": 0,
            "attempts": [
                {
                    "attempt_number": 1,
                    "started_at": datetime.now(UTC),
                    "status": JobStatus.SUCCESS.value,
                    "status_code": 200,
                    "latency_ms": 150.5,
                    "response_size_bytes": 1024,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {"success": True},
                    "error_message": None,
                }
            ],
        }
        
        job_id = await create_job_record(schedule.id, 1, request_result)
        
        assert job_id is not None


@pytest.mark.asyncio
async def test_create_job_record_with_error(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, _, schedule = await create_test_data_chain(test_db)
        
        request_result = {
            "status": JobStatus.ERROR.value,
            "status_code": None,
            "latency_ms": 50.0,
            "response_size_bytes": None,
            "started_at": datetime.now(UTC),
            "request_headers": None,
            "request_body": None,
            "response_headers": None,
            "response_body": None,
            "error_message": "Connection error",
            "redirected": False,
            "redirect_count": 0,
            "attempts": [],
        }
        
        job_id = await create_job_record(schedule.id, 1, request_result)
        
        assert job_id is not None

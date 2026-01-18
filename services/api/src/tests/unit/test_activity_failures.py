import pytest
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import OperationalError, DatabaseError

from temporal.activities import (
    get_schedule_and_target,
    execute_http_request,
    create_job_record,
)
from enums.job_status import JobStatus
from tests.helpers.db_helpers import create_test_data_chain
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_get_schedule_and_target_db_failure(test_db):
    with mock_session(test_db, "temporal.activities"):
        schedule_id = uuid4()
        
        with patch('temporal.activities.get_session') as mock_get_session:
            mock_session_ctx = AsyncMock()
            mock_session_ctx.__aenter__.side_effect = OperationalError("Database connection failed", None, None)
            mock_get_session.return_value = mock_session_ctx
            
            with pytest.raises(Exception):
                await get_schedule_and_target(schedule_id)


@pytest.mark.asyncio
async def test_get_schedule_and_target_schedule_not_found_mid_execution(test_db):
    with mock_session(test_db, "temporal.activities"):
        schedule_id = uuid4()
        
        result = await get_schedule_and_target(schedule_id)
        
        assert result.get("deleted") is True


@pytest.mark.asyncio
async def test_create_job_record_db_failure(test_db):
    with mock_session(test_db, "temporal.activities"):
        schedule_id = uuid4()
        
        request_result = {
            "status": JobStatus.SUCCESS.value,
            "status_code": 200,
            "latency_ms": 100.0,
            "response_size_bytes": 1024,
            "started_at": datetime.now(UTC),
            "request_headers": {},
            "request_body": None,
            "response_headers": {},
            "response_body": {},
            "error_message": None,
            "redirected": False,
            "redirect_count": 0,
            "attempts": [],
        }
        
        with patch('temporal.activities.get_session') as mock_get_session:
            mock_session_ctx = AsyncMock()
            mock_session_ctx.__aenter__.side_effect = DatabaseError("Database write failed", None, None)
            mock_get_session.return_value = mock_session_ctx
            
            with pytest.raises(Exception):
                await create_job_record(schedule_id, 1, request_result)


@pytest.mark.asyncio
async def test_create_job_record_partial_failure(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, _, schedule = await create_test_data_chain(test_db)
        
        request_result = {
            "status": JobStatus.SUCCESS.value,
            "status_code": 200,
            "latency_ms": 100.0,
            "response_size_bytes": 1024,
            "started_at": datetime.now(UTC),
            "request_headers": {},
            "request_body": None,
            "response_headers": {},
            "response_body": {},
            "error_message": None,
            "redirected": False,
            "redirect_count": 0,
            "attempts": [
                {
                    "attempt_number": 1,
                    "started_at": datetime.now(UTC),
                    "status": JobStatus.SUCCESS.value,
                    "status_code": 200,
                    "latency_ms": 100.0,
                    "response_size_bytes": 1024,
                    "response_headers": {},
                    "response_body": {},
                    "error_message": None,
                }
            ],
        }
        
        job_id = await create_job_record(schedule_id=schedule.id, run_number=1, request_result=request_result)
        assert job_id is not None


@pytest.mark.asyncio
async def test_execute_http_request_network_complete_failure():
    import httpx
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.side_effect = Exception("Network interface down")
        mock_client.return_value = mock_instance
        
        with pytest.raises(Exception):
            await execute_http_request(
                url="https://api.example.com/test",
                method="GET",
                headers=None,
                body=None,
            )


@pytest.mark.asyncio
async def test_execute_http_request_ssl_failure():
    import httpx
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("SSL certificate verification failed"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.CONNECTION_ERROR.value


@pytest.mark.asyncio
async def test_execute_http_request_intermittent_network():
    import httpx
    
    call_count = 0
    
    async def intermittent_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 1:
            raise httpx.ConnectError("Network unreachable")
        
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
        mock_instance.get = AsyncMock(side_effect=intermittent_failure)
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=3,
            retry_delay_seconds=0,
        )
        
        assert result["status"] == JobStatus.SUCCESS.value
        assert call_count >= 2


@pytest.mark.asyncio
async def test_create_job_record_with_large_response():
    with patch('temporal.activities.get_session') as mock_get_session:
        mock_session_obj = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session_obj
        mock_session_ctx.__aexit__.return_value = None
        mock_get_session.return_value = mock_session_ctx
        
        schedule_id = uuid4()
        
        large_response_body = {"data": "x" * 1000000}
        
        request_result = {
            "status": JobStatus.SUCCESS.value,
            "status_code": 200,
            "latency_ms": 5000.0,
            "response_size_bytes": 1000000,
            "started_at": datetime.now(UTC),
            "request_headers": {},
            "request_body": None,
            "response_headers": {},
            "response_body": large_response_body,
            "error_message": None,
            "redirected": False,
            "redirect_count": 0,
            "attempts": [],
        }
        
        mock_job = MagicMock()
        mock_job.id = uuid4()
        mock_session_obj.add = MagicMock()
        mock_session_obj.commit = AsyncMock()
        mock_session_obj.refresh = AsyncMock()
        
        with patch('temporal.activities.JobModel', return_value=mock_job):
            job_id = await create_job_record(schedule_id, 1, request_result)
            assert job_id == mock_job.id


@pytest.mark.asyncio
async def test_get_schedule_and_target_target_deleted_mid_execution(test_db):
    with mock_session(test_db, "temporal.activities"):
        _, target, schedule = await create_test_data_chain(test_db)
        
        with patch('temporal.activities.select') as mock_select:
            def side_effect_select(model):
                if model.__name__ == 'Target':
                    mock_result = AsyncMock()
                    mock_result.scalar_one_or_none.return_value = None
                    return mock_result
                return MagicMock()
            
            with pytest.raises(ValueError) as exc_info:
                await get_schedule_and_target(schedule.id)
            assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_http_request_max_redirects():
    import httpx
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=httpx.TooManyRedirects("Too many redirects"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
            follow_redirects=True,
        )
        
        assert result["status"] == JobStatus.ERROR.value
        assert "redirect" in result["error_message"].lower()


@pytest.mark.asyncio
async def test_execute_http_request_response_too_large():
    import httpx
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(side_effect=Exception("Response too large"))
        mock_client.return_value = mock_instance
        
        result = await execute_http_request(
            url="https://api.example.com/test",
            method="GET",
            headers=None,
            body=None,
            retry_count=0,
        )
        
        assert result["status"] == JobStatus.ERROR.value

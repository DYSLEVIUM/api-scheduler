import pytest
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from domains.runs.service import RunService
from enums.job_status import JobStatus
from models.job import Job as JobPydantic


@pytest.mark.asyncio
async def test_get_run_by_id_success():
    service = RunService()
    run_id = uuid4()
    
    mock_db_run = AsyncMock()
    mock_db_run.to_pydantic_model = lambda: JobPydantic(
        id=run_id,
        schedule_id=uuid4(),
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
    )
    
    mock_attempts = []
    
    with patch.object(service.repository, 'get_run_by_id', return_value=(mock_db_run, mock_attempts)):
        result = await service.get_run_by_id(run_id)
        assert result.id == run_id


@pytest.mark.asyncio
async def test_get_run_by_id_with_attempts():
    service = RunService()
    run_id = uuid4()
    job_id = uuid4()
    
    mock_db_run = AsyncMock()
    mock_db_run.to_pydantic_model = lambda: JobPydantic(
        id=run_id,
        schedule_id=uuid4(),
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
    )
    
    mock_attempt = AsyncMock()
    mock_attempt.to_pydantic_model = lambda: {
        "id": uuid4(),
        "job_id": job_id,
        "attempt_number": 1,
        "started_at": datetime.now(UTC),
        "status": JobStatus.SUCCESS.value,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    mock_attempts = [mock_attempt]
    
    with patch.object(service.repository, 'get_run_by_id', return_value=(mock_db_run, mock_attempts)):
        result = await service.get_run_by_id(run_id)
        assert result.id == run_id


@pytest.mark.asyncio
async def test_get_run_by_id_not_found():
    service = RunService()
    run_id = uuid4()
    
    with patch.object(service.repository, 'get_run_by_id', side_effect=Exception("Run not found")):
        with pytest.raises(Exception) as exc_info:
            await service.get_run_by_id(run_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_runs_by_schedule_id():
    service = RunService()
    schedule_id = uuid4()
    
    mock_db_run = AsyncMock()
    mock_db_run.to_pydantic_model = lambda: JobPydantic(
        id=uuid4(),
        schedule_id=schedule_id,
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
    )
    
    runs = [(mock_db_run, "Test Schedule")]
    
    with patch.object(service.repository, 'get_runs_by_schedule_id', return_value=runs):
        result = await service.get_runs_by_schedule_id(schedule_id)
        assert len(result) == 1


@pytest.mark.asyncio
async def test_get_runs_by_schedule_id_with_filters():
    service = RunService()
    schedule_id = uuid4()
    
    with patch.object(service.repository, 'get_runs_by_schedule_id', return_value=[]):
        result = await service.get_runs_by_schedule_id(
            schedule_id,
            status_filter=JobStatus.SUCCESS,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC)
        )
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_all_runs():
    service = RunService()
    
    mock_db_run = AsyncMock()
    mock_db_run.to_pydantic_model = lambda: JobPydantic(
        id=uuid4(),
        schedule_id=uuid4(),
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
    )
    
    runs = [(mock_db_run, "Test Schedule")]
    
    with patch.object(service.repository, 'get_all_runs', return_value=runs):
        result = await service.get_all_runs()
        assert len(result) == 1


@pytest.mark.asyncio
async def test_get_all_runs_with_filters():
    service = RunService()
    
    with patch.object(service.repository, 'get_all_runs', return_value=[]):
        result = await service.get_all_runs(
            status_filter=JobStatus.ERROR,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC)
        )
        assert len(result) == 0

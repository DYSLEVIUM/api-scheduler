from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from domains.jobs.service import JobService
from enums.job_status import JobStatus
from models.job import Job as JobPydantic


@pytest.mark.asyncio
async def test_create_job_success():
    service = JobService()
    schedule_id = uuid4()

    job = JobPydantic(
        schedule_id=schedule_id,
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
        status_code=200,
        latency_ms=150.5,
        response_size_bytes=1024,
    )

    mock_db_job = AsyncMock()
    mock_db_job.to_pydantic_model = lambda: job

    with patch.object(service.repository, 'create_job', return_value=mock_db_job):
        result = await service.create_job(job)
        assert result.schedule_id == schedule_id
        assert result.run_number == 1
        assert result.status == JobStatus.SUCCESS


@pytest.mark.asyncio
async def test_create_job_failure():
    service = JobService()
    schedule_id = uuid4()

    job = JobPydantic(
        schedule_id=schedule_id,
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.ERROR,
    )

    with patch.object(service.repository, 'create_job', side_effect=Exception("Database error")):
        with pytest.raises(Exception) as exc_info:
            await service.create_job(job)
        assert "Database error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_job_by_id_success():
    service = JobService()
    job_id = uuid4()

    job = JobPydantic(
        id=job_id,
        schedule_id=uuid4(),
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
    )

    mock_db_job = AsyncMock()
    mock_db_job.to_pydantic_model = lambda: job

    with patch.object(service.repository, 'get_job_by_id', return_value=mock_db_job):
        result = await service.get_job_by_id(job_id)
        assert result.id == job_id


@pytest.mark.asyncio
async def test_get_job_by_id_not_found():
    service = JobService()
    job_id = uuid4()

    with patch.object(service.repository, 'get_job_by_id', side_effect=Exception("Job not found")):
        with pytest.raises(Exception) as exc_info:
            await service.get_job_by_id(job_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_jobs_by_schedule_id():
    service = JobService()
    schedule_id = uuid4()

    jobs = [
        AsyncMock(to_pydantic_model=lambda: JobPydantic(
            id=uuid4(),
            schedule_id=schedule_id,
            run_number=1,
            started_at=datetime.now(UTC),
            status=JobStatus.SUCCESS,
        )),
        AsyncMock(to_pydantic_model=lambda: JobPydantic(
            id=uuid4(),
            schedule_id=schedule_id,
            run_number=2,
            started_at=datetime.now(UTC),
            status=JobStatus.SUCCESS,
        ))
    ]

    with patch.object(service.repository, 'get_jobs_by_schedule_id', return_value=jobs):
        result = await service.get_jobs_by_schedule_id(schedule_id)
        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_jobs_by_schedule_id_with_filters():
    service = JobService()
    schedule_id = uuid4()

    with patch.object(service.repository, 'get_jobs_by_schedule_id', return_value=[]):
        result = await service.get_jobs_by_schedule_id(
            schedule_id,
            status_filter=JobStatus.SUCCESS,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC)
        )
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_all_jobs():
    service = JobService()

    jobs = [
        AsyncMock(to_pydantic_model=lambda: JobPydantic(
            id=uuid4(),
            schedule_id=uuid4(),
            run_number=1,
            started_at=datetime.now(UTC),
            status=JobStatus.SUCCESS,
        ))
    ]

    with patch.object(service.repository, 'get_all_jobs', return_value=jobs):
        result = await service.get_all_jobs()
        assert len(result) == 1


@pytest.mark.asyncio
async def test_get_all_jobs_with_filters():
    service = JobService()

    with patch.object(service.repository, 'get_all_jobs', return_value=[]):
        result = await service.get_all_jobs(
            status_filter=JobStatus.ERROR,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC)
        )
        assert len(result) == 0

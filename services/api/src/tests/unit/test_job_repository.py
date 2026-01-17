import pytest
from datetime import UTC, datetime
from uuid import uuid4

from domains.jobs.repository import JobRepository
from enums.job_status import JobStatus
from models.job import Job as JobPydantic
from tests.helpers.db_helpers import (
    create_test_data_chain,
    create_test_job,
)
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_create_job(test_db):
    with mock_session(test_db, "domains.jobs.repository"):
        repo = JobRepository()
        _, _, schedule = await create_test_data_chain(test_db)

        job = JobPydantic(
            schedule_id=schedule.id,
            run_number=1,
            started_at=datetime.now(UTC),
            status=JobStatus.SUCCESS,
            status_code=200,
            latency_ms=150.5,
            response_size_bytes=1024,
        )

        db_job = await repo.create_job(job)
        assert db_job.schedule_id == schedule.id
        assert db_job.run_number == 1
        assert db_job.status == JobStatus.SUCCESS
        assert db_job.status_code == 200


@pytest.mark.asyncio
async def test_get_job_by_id(test_db):
    with mock_session(test_db, "domains.jobs.repository"):
        repo = JobRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        job_model = await create_test_job(test_db, schedule.id)

        db_job = await repo.get_job_by_id(job_model.id)
        assert db_job.id == job_model.id
        assert db_job.run_number == 1


@pytest.mark.asyncio
async def test_get_job_by_id_not_found(test_db):
    with mock_session(test_db, "domains.jobs.repository"):
        repo = JobRepository()
        fake_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await repo.get_job_by_id(fake_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_jobs_by_schedule_id(test_db):
    with mock_session(test_db, "domains.jobs.repository"):
        repo = JobRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id, run_number=1)
        await create_test_job(test_db, schedule.id, run_number=2)

        jobs = await repo.get_jobs_by_schedule_id(schedule.id)
        assert len(jobs) == 2

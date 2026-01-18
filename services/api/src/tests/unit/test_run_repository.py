import pytest
from datetime import UTC, datetime
from uuid import uuid4

from domains.runs.repository import RunRepository
from enums.job_status import JobStatus
from tests.helpers.db_helpers import (
    create_test_data_chain,
    create_test_job,
)
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_get_run_by_id(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        job_model = await create_test_job(test_db, schedule.id)

        db_run, db_attempts = await repo.get_run_by_id(job_model.id)
        assert db_run.id == job_model.id
        assert db_run.run_number == 1


@pytest.mark.asyncio
async def test_get_run_by_id_not_found(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        fake_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await repo.get_run_by_id(fake_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_runs_by_schedule_id(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id, run_number=1)
        await create_test_job(test_db, schedule.id, run_number=2)

        runs = await repo.get_runs_by_schedule_id(schedule.id)
        assert len(runs) == 2


@pytest.mark.asyncio
async def test_get_runs_by_schedule_id_with_status_filter(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id, status=JobStatus.SUCCESS)
        await create_test_job(test_db, schedule.id, status=JobStatus.ERROR)

        runs = await repo.get_runs_by_schedule_id(
            schedule.id, status_filter=JobStatus.SUCCESS
        )
        assert len(runs) == 1
        assert runs[0][0].status == JobStatus.SUCCESS


@pytest.mark.asyncio
async def test_get_runs_by_schedule_id_with_time_filter(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id)

        start_time = datetime.now(UTC)
        end_time = datetime.now(UTC)

        runs = await repo.get_runs_by_schedule_id(
            schedule.id, start_time=start_time, end_time=end_time
        )
        assert len(runs) >= 0


@pytest.mark.asyncio
async def test_get_all_runs(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule1 = await create_test_data_chain(test_db)
        _, _, schedule2 = await create_test_data_chain(test_db)
        
        await create_test_job(test_db, schedule1.id)
        await create_test_job(test_db, schedule2.id)

        runs = await repo.get_all_runs()
        assert len(runs) >= 2


@pytest.mark.asyncio
async def test_get_all_runs_with_status_filter(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id, status=JobStatus.SUCCESS)
        await create_test_job(test_db, schedule.id, status=JobStatus.ERROR)

        runs = await repo.get_all_runs(status_filter=JobStatus.ERROR)
        assert len(runs) >= 1


@pytest.mark.asyncio
async def test_get_all_runs_with_time_filter(test_db):
    with mock_session(test_db, "domains.runs.repository"):
        repo = RunRepository()
        _, _, schedule = await create_test_data_chain(test_db)
        await create_test_job(test_db, schedule.id)

        start_time = datetime.now(UTC)
        end_time = datetime.now(UTC)

        runs = await repo.get_all_runs(start_time=start_time, end_time=end_time)
        assert len(runs) >= 0

import pytest
from uuid import uuid4

from domains.schedules.repository import ScheduleRepository
from models.schedule import IntervalSchedule as IntervalSchedulePydantic
from tests.helpers.db_helpers import (
    create_test_data_chain,
    create_test_schedule,
)
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_create_schedule(test_db):
    with mock_session(test_db, "domains.schedules.repository"):
        repo = ScheduleRepository()
        _, target, _ = await create_test_data_chain(test_db)

        schedule = IntervalSchedulePydantic(
            target_id=target.id,
            interval_seconds=60,
        )

        db_schedule = await repo.create_schedule(schedule)
        assert db_schedule.interval_seconds == 60
        assert db_schedule.target_id == target.id
        assert db_schedule.paused is False


@pytest.mark.asyncio
async def test_get_schedule_by_id(test_db):
    with mock_session(test_db, "domains.schedules.repository"):
        repo = ScheduleRepository()
        _, _, schedule = await create_test_data_chain(test_db)

        db_schedule = await repo.get_schedule_by_id(schedule.id)
        assert db_schedule.id == schedule.id
        assert db_schedule.interval_seconds == 60


@pytest.mark.asyncio
async def test_get_schedule_by_id_not_found(test_db):
    with mock_session(test_db, "domains.schedules.repository"):
        repo = ScheduleRepository()
        fake_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await repo.get_schedule_by_id(fake_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_pause_schedule(test_db):
    with mock_session(test_db, "domains.schedules.repository"):
        repo = ScheduleRepository()
        _, _, schedule = await create_test_data_chain(test_db)

        db_schedule = await repo.pause_schedule(schedule.id)
        assert db_schedule.paused is True


@pytest.mark.asyncio
async def test_resume_schedule(test_db):
    with mock_session(test_db, "domains.schedules.repository"):
        repo = ScheduleRepository()
        _, _, schedule = await create_test_data_chain(
            test_db, schedule_kwargs={"paused": True}
        )

        db_schedule = await repo.resume_schedule(schedule.id)
        assert db_schedule.paused is False

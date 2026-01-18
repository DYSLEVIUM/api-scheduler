from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from domains.jobs.service import JobService
from domains.schedules.service import ScheduleService
from domains.targets.service import TargetService
from models.schedule import IntervalSchedule as IntervalSchedulePydantic
from models.target import Target as TargetPydantic
from sqlalchemy.exc import DatabaseError, OperationalError


@pytest.mark.asyncio
async def test_schedule_creation_when_db_down():
    service = ScheduleService()

    schedule = IntervalSchedulePydantic(
        target_id=uuid4(),
        interval_seconds=60,
    )

    with patch.object(
        service.repository,
        'create_schedule',
        side_effect=OperationalError("Database connection lost", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.create_schedule(schedule)
        assert "connection" in str(exc_info.value).lower(
        ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_schedule_creation_when_temporal_down():
    service = ScheduleService()
    target_id = uuid4()

    schedule = IntervalSchedulePydantic(
        target_id=target_id,
        interval_seconds=60,
    )

    mock_db_schedule = AsyncMock()
    mock_db_schedule.id = uuid4()
    mock_db_schedule.paused = False
    mock_db_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"

    with patch.object(service.repository, 'create_schedule', return_value=mock_db_schedule):
        with patch('temporal.client.get_temporal_client', side_effect=Exception("Temporal unavailable")):
            with pytest.raises(Exception) as exc_info:
                await service.create_schedule(schedule)
            assert "temporal" in str(exc_info.value).lower(
            ) or "unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_schedule_when_db_down():
    service = ScheduleService()
    schedule_id = uuid4()

    with patch.object(
        service.repository,
        'get_schedule_by_id',
        side_effect=OperationalError("Database connection lost", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.get_schedule_by_id(schedule_id)
        assert "connection" in str(exc_info.value).lower(
        ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_pause_schedule_when_db_down():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"

    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch.object(
            service.repository,
            'pause_schedule',
            side_effect=OperationalError(
                "Database connection lost", None, None)
        ):
            with patch('temporal.client.get_temporal_client'):
                with pytest.raises(Exception) as exc_info:
                    await service.pause_schedule(schedule_id)
                assert "connection" in str(exc_info.value).lower(
                ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_pause_schedule_when_temporal_down():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=True,
    )

    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client', side_effect=Exception("Temporal unavailable")):
            with pytest.raises(Exception):
                await service.pause_schedule(schedule_id)


@pytest.mark.asyncio
async def test_resume_schedule_when_temporal_down():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = None
    mock_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"

    with patch.object(service.repository, 'resume_schedule', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client', side_effect=Exception("Temporal unavailable")):
            with pytest.raises(Exception) as exc_info:
                await service.resume_schedule(schedule_id)
            assert "temporal" in str(exc_info.value).lower(
            ) or "unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_delete_schedule_when_db_down_after_temporal():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"

    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client'):
            with patch('domains.jobs.repository.JobRepository.delete_jobs_by_schedule_id'):
                with patch.object(
                    service.repository,
                    'delete_schedule',
                    side_effect=DatabaseError("Database error", None, None)
                ):
                    with pytest.raises(Exception) as exc_info:
                        await service.delete_schedule(schedule_id)


@pytest.mark.asyncio
async def test_create_job_when_db_down():
    from models.job import Job as JobPydantic

    service = JobService()

    job = JobPydantic(
        schedule_id=uuid4(),
        run_number=1,
        started_at=datetime.now(UTC),
        status="success",
    )

    with patch.object(
        service.repository,
        'create_job',
        side_effect=OperationalError("Database connection lost", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.create_job(job)
        assert "connection" in str(exc_info.value).lower(
        ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_jobs_when_db_down():
    service = JobService()

    with patch.object(
        service.repository,
        'get_all_jobs',
        side_effect=OperationalError("Database connection lost", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.get_all_jobs()


@pytest.mark.asyncio
async def test_create_target_when_db_down():
    service = TargetService()

    target = TargetPydantic(
        name="Test Target",
        url=urlparse("https://api.example.com/test"),
        method="GET",
        headers={},
    )

    with patch.object(
        service.repository,
        'create_target',
        side_effect=OperationalError("Database connection lost", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.create_target(target)
        assert "connection" in str(exc_info.value).lower(
        ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_db_connection_lost_during_transaction():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"

    call_count = 0

    def side_effect_func(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_schedule
        raise OperationalError("Connection lost mid-transaction", None, None)

    with patch.object(service.repository, 'get_schedule_by_id', side_effect=side_effect_func):
        await service.get_schedule_by_id(schedule_id)

        with pytest.raises(Exception):
            await service.get_schedule_by_id(schedule_id)


@pytest.mark.asyncio
async def test_temporal_connection_lost_during_workflow_start():
    service = ScheduleService()
    target_id = uuid4()

    schedule = IntervalSchedulePydantic(
        target_id=target_id,
        interval_seconds=60,
    )

    mock_db_schedule = AsyncMock()
    mock_db_schedule.id = uuid4()
    mock_db_schedule.paused = False
    mock_db_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"

    mock_client = AsyncMock()

    with patch.object(service.repository, 'create_schedule', return_value=mock_db_schedule):
        with patch('temporal.client.get_temporal_client', return_value=mock_client):
            with patch('temporal.client.start_schedule_workflow', side_effect=Exception("Connection timeout")):
                with pytest.raises(Exception) as exc_info:
                    await service.create_schedule(schedule)


@pytest.mark.asyncio
async def test_db_down_during_schedule_pause():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"

    mock_client = AsyncMock()

    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client', return_value=mock_client):
            with patch('temporal.client.terminate_schedule_workflow'):
                with patch.object(
                    service.repository,
                    'pause_schedule',
                    side_effect=DatabaseError("Database locked", None, None)
                ):
                    with pytest.raises(Exception):
                        await service.pause_schedule(schedule_id)


@pytest.mark.asyncio
async def test_db_down_during_schedule_resume():
    service = ScheduleService()
    schedule_id = uuid4()

    with patch.object(
        service.repository,
        'resume_schedule',
        side_effect=OperationalError("Database unavailable", None, None)
    ):
        with pytest.raises(Exception):
            await service.resume_schedule(schedule_id)


@pytest.mark.asyncio
async def test_temporal_workflow_already_terminated():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=True,
    )

    mock_client = AsyncMock()

    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client', return_value=mock_client):
            with patch('temporal.client.terminate_schedule_workflow', side_effect=Exception("Workflow not found")):
                with patch.object(service.repository, 'pause_schedule', return_value=mock_schedule):
                    result = await service.pause_schedule(schedule_id)
                    assert result.paused is True


@pytest.mark.asyncio
async def test_partial_failure_workflow_state_inconsistent():
    service = ScheduleService()
    schedule_id = uuid4()

    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"

    with patch.object(service.repository, 'resume_schedule', return_value=mock_schedule):
        with patch('temporal.client.get_temporal_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            mock_handle = AsyncMock()
            mock_handle.describe = AsyncMock(
                side_effect=Exception("Workflow in unknown state"))
            mock_client.get_workflow_handle = lambda workflow_id: mock_handle

            with patch('temporal.client.start_schedule_workflow', return_value="new-workflow-id"):
                with patch.object(service.repository, 'update_workflow_id'):
                    result = await service.resume_schedule(schedule_id)


@pytest.mark.asyncio
async def test_db_connection_pool_exhausted():
    service = JobService()

    with patch.object(
        service.repository,
        'get_all_jobs',
        side_effect=OperationalError("connection pool exhausted", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.get_all_jobs()
        assert "pool" in str(exc_info.value).lower(
        ) or "connection" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_db_transaction_deadlock():
    service = ScheduleService()
    schedule_id = uuid4()

    with patch.object(
        service.repository,
        'get_schedule_by_id',
        side_effect=DatabaseError("Deadlock detected", None, None)
    ):
        with pytest.raises(Exception) as exc_info:
            await service.get_schedule_by_id(schedule_id)
        assert "deadlock" in str(exc_info.value).lower(
        ) or "database" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_temporal_task_queue_unavailable():
    service = ScheduleService()
    target_id = uuid4()

    schedule = IntervalSchedulePydantic(
        target_id=target_id,
        interval_seconds=60,
    )

    mock_db_schedule = AsyncMock()
    mock_db_schedule.id = uuid4()
    mock_db_schedule.paused = False
    mock_db_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"

    with patch.object(service.repository, 'create_schedule', return_value=mock_db_schedule):
        with patch('temporal.client.get_temporal_client'):
            with patch('temporal.client.start_schedule_workflow', side_effect=Exception("Task queue not found")):
                with pytest.raises(Exception) as exc_info:
                    await service.create_schedule(schedule)
                assert "task queue" in str(exc_info.value).lower(
                ) or "not found" in str(exc_info.value).lower()

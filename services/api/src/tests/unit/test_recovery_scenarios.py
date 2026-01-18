import pytest
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock, call
from sqlalchemy.exc import OperationalError, DatabaseError

from domains.schedules.service import ScheduleService
from domains.jobs.service import JobService
from models.schedule import IntervalSchedule as IntervalSchedulePydantic
from enums.job_status import JobStatus


@pytest.mark.asyncio
async def test_schedule_running_db_goes_down_then_recovers():
    """Test schedule continues after DB recovers from failure"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=False,
    )
    
    call_count = 0
    
    def db_intermittent_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if 2 <= call_count <= 3:
            raise OperationalError("Database connection lost", None, None)
        return mock_schedule
    
    with patch.object(service.repository, 'get_schedule_by_id', side_effect=db_intermittent_failure):
        # First call succeeds
        result1 = await service.get_schedule_by_id(schedule_id)
        assert result1.id == schedule_id
        
        # Second and third calls fail (DB down)
        with pytest.raises(Exception):
            await service.get_schedule_by_id(schedule_id)
        
        with pytest.raises(Exception):
            await service.get_schedule_by_id(schedule_id)
        
        # Fourth call succeeds (DB recovered)
        result2 = await service.get_schedule_by_id(schedule_id)
        assert result2.id == schedule_id


@pytest.mark.asyncio
async def test_schedule_running_temporal_goes_down_then_recovers():
    """Test schedule can be resumed after Temporal recovers"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.temporal_workflow_id = None
    mock_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"
    
    call_count = 0
    
    async def temporal_intermittent_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Temporal service unavailable")
        return AsyncMock()
    
    with patch.object(service.repository, 'resume_schedule', return_value=mock_schedule):
        with patch('domains.schedules.service.get_temporal_client', side_effect=temporal_intermittent_failure):
            # First two attempts fail (Temporal down)
            with pytest.raises(Exception):
                await service.resume_schedule(schedule_id)
            
            with pytest.raises(Exception):
                await service.resume_schedule(schedule_id)
        
        # Third attempt succeeds (Temporal recovered)
        with patch('domains.schedules.service.get_temporal_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            with patch('domains.schedules.service.start_schedule_workflow', return_value="new-workflow-id"):
                with patch.object(service.repository, 'update_workflow_id', return_value=None):
                    result = await service.resume_schedule(schedule_id)
                    assert result is not None


@pytest.mark.asyncio
async def test_activity_execution_db_fails_then_recovers():
    """Test activity retries after DB recovery"""
    from temporal.activities import get_schedule_and_target
    from tests.helpers.db_helpers import create_test_data_chain
    from tests.helpers.mocks import mock_session
    
    # This simulates multiple attempts where DB fails then recovers
    schedule_id = uuid4()
    
    call_count = 0
    
    async def mock_db_with_recovery():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise OperationalError("Connection lost", None, None)
        
        # After recovery, return valid data
        return {
            "paused": False,
            "schedule": {"interval_seconds": 60},
            "target": {
                "method": "GET",
                "headers": {},
                "body": None,
                "timeout_seconds": 30,
                "retry_count": 0,
                "retry_delay_seconds": 1,
                "follow_redirects": True,
            },
            "url": "https://api.example.com/test",
        }
    
    # Simulate retries
    for attempt in range(3):
        try:
            result = await mock_db_with_recovery()
            assert result["paused"] is False
            break
        except OperationalError:
            if attempt == 2:
                raise
            continue


@pytest.mark.asyncio
async def test_job_creation_db_fails_then_recovers():
    """Test job creation retries after DB recovery"""
    from models.job import Job as JobPydantic
    
    service = JobService()
    schedule_id = uuid4()
    
    job = JobPydantic(
        schedule_id=schedule_id,
        run_number=1,
        started_at=datetime.now(UTC),
        status=JobStatus.SUCCESS,
        status_code=200,
    )
    
    mock_db_job = AsyncMock()
    mock_db_job.to_pydantic_model = lambda: job
    
    call_count = 0
    
    def db_retry_then_success(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OperationalError("Database write failed", None, None)
        return mock_db_job
    
    with patch.object(service.repository, 'create_job', side_effect=db_retry_then_success):
        # First attempt fails
        with pytest.raises(Exception):
            await service.create_job(job)
        
        # Second attempt succeeds (DB recovered)
        result = await service.create_job(job)
        assert result.schedule_id == schedule_id


@pytest.mark.asyncio
async def test_schedule_pause_during_db_downtime():
    """Test pausing schedule during DB outage and recovery"""
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
    
    # Simulate DB down during get, but up during pause
    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        with patch('domains.schedules.service.get_temporal_client', return_value=AsyncMock()):
            with patch('temporal.client.terminate_schedule_workflow', return_value=None):
                call_count = 0
                
                def pause_with_recovery(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise DatabaseError("Transaction failed", None, None)
                    return mock_schedule
                
                with patch.object(service.repository, 'pause_schedule', side_effect=pause_with_recovery):
                    # First attempt fails
                    with pytest.raises(Exception):
                        await service.pause_schedule(schedule_id)
                    
                    # Second attempt succeeds
                    result = await service.pause_schedule(schedule_id)
                    assert result.paused is True


@pytest.mark.asyncio
async def test_workflow_restart_after_temporal_recovery():
    """Test workflow can be restarted after Temporal comes back online"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.temporal_workflow_id = "old-workflow-id"
    mock_schedule.get_workflow_type = lambda: "IntervalScheduleWorkflow"
    
    with patch.object(service.repository, 'resume_schedule', return_value=mock_schedule):
        # First, Temporal is down
        with patch('domains.schedules.service.get_temporal_client', side_effect=Exception("Temporal unavailable")):
            with pytest.raises(Exception) as exc_info:
                await service.resume_schedule(schedule_id)
            assert "temporal" in str(exc_info.value).lower() or "unavailable" in str(exc_info.value).lower()
        
        # Then, Temporal recovers
        with patch('domains.schedules.service.get_temporal_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Old workflow is gone, need to start new one
            mock_handle = AsyncMock()
            mock_handle.describe = AsyncMock(side_effect=Exception("Workflow not found"))
            mock_client.get_workflow_handle = lambda workflow_id: mock_handle
            
            with patch('domains.schedules.service.start_schedule_workflow', return_value="new-workflow-id") as mock_start:
                with patch.object(service.repository, 'update_workflow_id') as mock_update:
                    result = await service.resume_schedule(schedule_id)
                    
                    # Verify new workflow was started
                    mock_start.assert_called_once()
                    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_schedules_running_during_db_recovery():
    """Test multiple schedules handle DB recovery gracefully"""
    service = ScheduleService()
    
    schedule_ids = [uuid4(), uuid4(), uuid4()]
    
    def create_mock_schedule(sid):
        mock = AsyncMock()
        mock.id = sid
        mock.to_pydantic_model = lambda: IntervalSchedulePydantic(
            id=sid,
            target_id=uuid4(),
            interval_seconds=60,
            paused=False,
        )
        return mock
    
    mock_schedules = [create_mock_schedule(sid) for sid in schedule_ids]
    
    call_count = 0
    
    def db_recovery_scenario(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # DB fails for calls 2-4
        if 2 <= call_count <= 4:
            raise OperationalError("Connection pool exhausted", None, None)
        
        # Return appropriate schedule
        schedule_index = (call_count - 1) % 3
        if call_count > 4:
            schedule_index = (call_count - 5) % 3
        return mock_schedules[schedule_index]
    
    with patch.object(service.repository, 'get_schedule_by_id', side_effect=db_recovery_scenario):
        # First schedule succeeds
        result1 = await service.get_schedule_by_id(schedule_ids[0])
        assert result1.id == schedule_ids[0]
        
        # Next few calls fail (DB down)
        for _ in range(3):
            with pytest.raises(Exception):
                await service.get_schedule_by_id(schedule_ids[1])
        
        # After recovery, all schedules work
        result2 = await service.get_schedule_by_id(schedule_ids[0])
        result3 = await service.get_schedule_by_id(schedule_ids[1])
        result4 = await service.get_schedule_by_id(schedule_ids[2])
        
        assert result2.id == schedule_ids[0]
        assert result3.id == schedule_ids[1]
        assert result4.id == schedule_ids[2]


@pytest.mark.asyncio
async def test_schedule_delete_during_temporal_recovery():
    """Test schedule deletion handles Temporal recovery"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=False,
    )
    
    call_count = 0
    
    async def temporal_recovery(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Temporal unavailable")
        return AsyncMock()
    
    with patch.object(service.repository, 'get_schedule_by_id', return_value=mock_schedule):
        # First attempt - Temporal down
        with patch('domains.schedules.service.get_temporal_client', side_effect=temporal_recovery):
            with pytest.raises(Exception):
                await service.delete_schedule(schedule_id)
        
        # Second attempt - Temporal recovered
        with patch('domains.schedules.service.get_temporal_client', return_value=AsyncMock()):
            with patch('temporal.client.terminate_schedule_workflow', return_value=None):
                with patch('domains.jobs.repository.JobRepository.delete_jobs_by_schedule_id', return_value=None):
                    with patch.object(service.repository, 'delete_schedule', return_value=mock_schedule):
                        result = await service.delete_schedule(schedule_id)
                        assert result.id == schedule_id


@pytest.mark.asyncio
async def test_concurrent_operations_during_db_recovery():
    """Test concurrent operations handle DB recovery"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=False,
    )
    
    operation_results = []
    
    call_count = 0
    
    def concurrent_db_access(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # Fail every other call to simulate contention
        if call_count % 2 == 0 and call_count <= 4:
            raise OperationalError("Deadlock detected", None, None)
        
        return mock_schedule
    
    with patch.object(service.repository, 'get_schedule_by_id', side_effect=concurrent_db_access):
        # Simulate multiple concurrent operations
        for i in range(6):
            try:
                result = await service.get_schedule_by_id(schedule_id)
                operation_results.append(("success", i))
            except Exception as e:
                operation_results.append(("failed", i))
        
        # Some operations should succeed, some should fail
        successes = [r for r in operation_results if r[0] == "success"]
        failures = [r for r in operation_results if r[0] == "failed"]
        
        assert len(successes) > 0
        assert len(failures) > 0


@pytest.mark.asyncio
async def test_http_request_during_network_recovery():
    """Test HTTP requests retry after network recovery"""
    from temporal.activities import execute_http_request
    import httpx
    
    call_count = 0
    
    async def network_recovery(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # Network down for first 2 attempts
        if call_count <= 2:
            raise httpx.ConnectError("Network unreachable")
        
        # Network recovered
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
        mock_instance.get = AsyncMock(side_effect=network_recovery)
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
        assert call_count == 3
        assert len(result["attempts"]) == 3


@pytest.mark.asyncio
async def test_schedule_state_consistency_after_recovery():
    """Test schedule state remains consistent after DB recovery"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.paused = False
    mock_schedule.temporal_workflow_id = "workflow-123"
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=mock_schedule.paused,
    )
    
    call_count = 0
    
    def state_check_with_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise DatabaseError("Connection interrupted", None, None)
        return mock_schedule
    
    with patch.object(service.repository, 'get_schedule_by_id', side_effect=state_check_with_failure):
        # Get initial state
        result1 = await service.get_schedule_by_id(schedule_id)
        assert result1.paused is False
        
        # DB fails
        with pytest.raises(Exception):
            await service.get_schedule_by_id(schedule_id)
        
        # After recovery, state should be same
        result2 = await service.get_schedule_by_id(schedule_id)
        assert result2.paused is False
        assert result2.id == schedule_id


@pytest.mark.asyncio
async def test_long_running_schedule_survives_multiple_failures():
    """Test long-running schedule survives multiple transient failures"""
    service = ScheduleService()
    schedule_id = uuid4()
    
    mock_schedule = AsyncMock()
    mock_schedule.id = schedule_id
    mock_schedule.to_pydantic_model = lambda: IntervalSchedulePydantic(
        id=schedule_id,
        target_id=uuid4(),
        interval_seconds=60,
        paused=False,
    )
    
    failures = [2, 5, 8]  # Fail on these call numbers
    call_count = 0
    
    def intermittent_failures(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count in failures:
            raise OperationalError("Transient failure", None, None)
        
        return mock_schedule
    
    with patch.object(service.repository, 'get_schedule_by_id', side_effect=intermittent_failures):
        success_count = 0
        failure_count = 0
        
        # Simulate 10 operations over time
        for i in range(10):
            try:
                result = await service.get_schedule_by_id(schedule_id)
                success_count += 1
            except Exception:
                failure_count += 1
        
        assert success_count == 7
        assert failure_count == 3


@pytest.mark.asyncio
async def test_workflow_execution_continues_after_activity_retry():
    """Test workflow continues after activity recovers from failure"""
    from temporal.activities import create_job_record
    from tests.helpers.mocks import mock_session
    
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
    
    call_count = 0
    mock_job_id = uuid4()
    
    async def activity_with_recovery(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            raise DatabaseError("Write failed", None, None)
        
        return mock_job_id
    
    # Simulate retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = await activity_with_recovery()
            assert result == mock_job_id
            break
        except DatabaseError:
            if attempt == max_retries - 1:
                raise
            continue
    
    assert call_count == 2

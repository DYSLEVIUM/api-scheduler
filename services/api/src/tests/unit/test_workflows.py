import pytest
from datetime import timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from temporal.workflows import IntervalScheduleWorkflow, WindowScheduleWorkflow
from temporal.activities import (
    get_schedule_and_target,
    execute_http_request,
    create_job_record,
)
from enums.job_status import JobStatus


@pytest.mark.asyncio
async def test_interval_schedule_workflow_basic():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create_job:
                        mock_get_schedule.return_value = {
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
                        
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        
                        mock_create_job.return_value = uuid4()
                        
                        handle = await env.client.start_workflow(
                            IntervalScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-interval-{schedule_id}",
                            task_queue="test-queue",
                        )
                        
                        await env.sleep(timedelta(seconds=5))
                        
                        await handle.cancel()


@pytest.mark.asyncio
async def test_interval_schedule_workflow_paused():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                mock_get_schedule.return_value = {"paused": True}
                
                handle = await env.client.start_workflow(
                    IntervalScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-interval-paused-{schedule_id}",
                    task_queue="test-queue",
                )
                
                await env.sleep(timedelta(seconds=5))
                
                await handle.cancel()


@pytest.mark.asyncio
async def test_interval_schedule_workflow_deleted():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                mock_get_schedule.return_value = {"deleted": True}
                
                handle = await env.client.start_workflow(
                    IntervalScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-interval-deleted-{schedule_id}",
                    task_queue="test-queue",
                )
                
                await handle.result()


@pytest.mark.asyncio
async def test_window_schedule_workflow_basic():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create_job:
                        mock_get_schedule.return_value = {
                            "paused": False,
                            "schedule": {
                                "interval_seconds": 30,
                                "duration_seconds": 120,
                            },
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
                        
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        
                        mock_create_job.return_value = uuid4()
                        
                        handle = await env.client.start_workflow(
                            WindowScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-window-{schedule_id}",
                            task_queue="test-queue",
                        )
                        
                        await env.sleep(timedelta(seconds=5))
                        
                        await handle.cancel()


@pytest.mark.asyncio
async def test_window_schedule_workflow_paused():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                mock_get_schedule.return_value = {"paused": True}
                
                handle = await env.client.start_workflow(
                    WindowScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-window-paused-{schedule_id}",
                    task_queue="test-queue",
                )
                
                await handle.result()


@pytest.mark.asyncio
async def test_window_schedule_workflow_deleted():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                mock_get_schedule.return_value = {"deleted": True}
                
                handle = await env.client.start_workflow(
                    WindowScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-window-deleted-{schedule_id}",
                    task_queue="test-queue",
                )
                
                await handle.result()


@pytest.mark.asyncio
async def test_window_schedule_workflow_completes_duration():
    schedule_id = uuid4()
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target, execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get_schedule:
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create_job:
                        mock_get_schedule.return_value = {
                            "paused": False,
                            "schedule": {
                                "interval_seconds": 10,
                                "duration_seconds": 25,
                            },
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
                        
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        
                        mock_create_job.return_value = uuid4()
                        
                        handle = await env.client.start_workflow(
                            WindowScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-window-complete-{schedule_id}",
                            task_queue="test-queue",
                        )
                        
                        await env.sleep(timedelta(seconds=30))
                        
                        result = await handle.result()
                        assert result is None

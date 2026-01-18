from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from enums.job_status import JobStatus
from temporal.activities import (create_job_record, execute_http_request,
                                 get_schedule_and_target)
from temporal.workflows import IntervalScheduleWorkflow, WindowScheduleWorkflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker


@pytest.mark.asyncio
async def test_workflow_paused_at_start():
    schedule_id = uuid4()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get:
                mock_get.return_value = {"paused": True}

                handle = await env.client.start_workflow(
                    IntervalScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-paused-{schedule_id}",
                    task_queue="test-queue",
                )

                await env.sleep(timedelta(seconds=35))
                await handle.cancel()


@pytest.mark.asyncio
async def test_workflow_deleted_at_start():
    schedule_id = uuid4()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get:
                mock_get.return_value = {"deleted": True}

                handle = await env.client.start_workflow(
                    IntervalScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-deleted-{schedule_id}",
                    task_queue="test-queue",
                )

                result = await handle.result()
                assert result is None


@pytest.mark.asyncio
async def test_workflow_paused_during_execution():
    schedule_id = uuid4()
    call_count = 0

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            def mock_get_schedule(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    return {
                        "paused": False,
                        "schedule": {"interval_seconds": 10},
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
                return {"paused": True}

            with patch('temporal.activities.get_schedule_and_target', side_effect=mock_get_schedule):
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create:
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        mock_create.return_value = uuid4()

                        handle = await env.client.start_workflow(
                            IntervalScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-pause-during-{schedule_id}",
                            task_queue="test-queue",
                        )

                        await env.sleep(timedelta(seconds=50))
                        await handle.cancel()


@pytest.mark.asyncio
async def test_workflow_deleted_during_execution():
    schedule_id = uuid4()
    call_count = 0

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            def mock_get_schedule(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    return {
                        "paused": False,
                        "schedule": {"interval_seconds": 10},
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
                return {"deleted": True}

            with patch('temporal.activities.get_schedule_and_target', side_effect=mock_get_schedule):
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create:
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        mock_create.return_value = uuid4()

                        handle = await env.client.start_workflow(
                            IntervalScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-delete-during-{schedule_id}",
                            task_queue="test-queue",
                        )

                        await env.sleep(timedelta(seconds=30))
                        result = await handle.result()
                        assert result is None


@pytest.mark.asyncio
async def test_window_workflow_paused_before_start():
    schedule_id = uuid4()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get:
                mock_get.return_value = {"paused": True}

                handle = await env.client.start_workflow(
                    WindowScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-window-paused-{schedule_id}",
                    task_queue="test-queue",
                )

                result = await handle.result()
                assert result is None


@pytest.mark.asyncio
async def test_window_workflow_deleted_before_start():
    schedule_id = uuid4()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get:
                mock_get.return_value = {"deleted": True}

                handle = await env.client.start_workflow(
                    WindowScheduleWorkflow.run,
                    schedule_id,
                    id=f"test-window-deleted-{schedule_id}",
                    task_queue="test-queue",
                )

                result = await handle.result()
                assert result is None


@pytest.mark.asyncio
async def test_window_workflow_paused_during_window():
    schedule_id = uuid4()
    call_count = 0

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            def mock_get_schedule(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "paused": False,
                        "schedule": {
                            "interval_seconds": 10,
                            "duration_seconds": 60,
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
                elif call_count <= 3:
                    return {
                        "paused": False,
                        "schedule": {
                            "interval_seconds": 10,
                            "duration_seconds": 60,
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
                return {"paused": True}

            with patch('temporal.activities.get_schedule_and_target', side_effect=mock_get_schedule):
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create:
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        mock_create.return_value = uuid4()

                        handle = await env.client.start_workflow(
                            WindowScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-window-pause-during-{schedule_id}",
                            task_queue="test-queue",
                        )

                        await env.sleep(timedelta(seconds=70))
                        result = await handle.result()
                        assert result is None


@pytest.mark.asyncio
async def test_window_workflow_deleted_during_window():
    schedule_id = uuid4()
    call_count = 0

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[WindowScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            def mock_get_schedule(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "paused": False,
                        "schedule": {
                            "interval_seconds": 10,
                            "duration_seconds": 60,
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
                elif call_count <= 2:
                    return {
                        "paused": False,
                        "schedule": {
                            "interval_seconds": 10,
                            "duration_seconds": 60,
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
                return {"deleted": True}

            with patch('temporal.activities.get_schedule_and_target', side_effect=mock_get_schedule):
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create:
                        mock_http.return_value = {
                            "status": JobStatus.SUCCESS.value,
                            "status_code": 200,
                            "latency_ms": 100.0,
                            "response_size_bytes": 1024,
                            "started_at": "2024-01-01T00:00:00",
                            "attempts": [],
                        }
                        mock_create.return_value = uuid4()

                        handle = await env.client.start_workflow(
                            WindowScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-window-delete-during-{schedule_id}",
                            task_queue="test-queue",
                        )

                        await env.sleep(timedelta(seconds=30))
                        result = await handle.result()
                        assert result is None


@pytest.mark.asyncio
async def test_workflow_cancellation():
    schedule_id = uuid4()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntervalScheduleWorkflow],
            activities=[get_schedule_and_target,
                        execute_http_request, create_job_record],
        ):
            with patch('temporal.activities.get_schedule_and_target') as mock_get:
                with patch('temporal.activities.execute_http_request') as mock_http:
                    with patch('temporal.activities.create_job_record') as mock_create:
                        mock_get.return_value = {
                            "paused": False,
                            "schedule": {"interval_seconds": 10},
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
                        mock_create.return_value = uuid4()

                        handle = await env.client.start_workflow(
                            IntervalScheduleWorkflow.run,
                            schedule_id,
                            id=f"test-cancel-{schedule_id}",
                            task_queue="test-queue",
                        )

                        await env.sleep(timedelta(seconds=15))
                        await handle.cancel()

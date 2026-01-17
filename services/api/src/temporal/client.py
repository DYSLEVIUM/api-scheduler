from uuid import UUID

from temporalio.client import Client
from temporalio.worker import Worker

from core.config import settings
from temporal.activities import (create_job_record, execute_http_request,
                                 get_schedule_and_target)
from temporal.workflows import IntervalScheduleWorkflow, WindowScheduleWorkflow


async def get_temporal_client() -> Client:
    return await Client.connect(
        target_host=settings.temporal_host,
        namespace=settings.temporal_namespace,
    )


async def start_schedule_workflow(
    schedule_id: UUID, schedule_type: str, client: Client | None = None
) -> str:
    if client is None:
        client = await get_temporal_client()

    workflow_id = f"schedule-{schedule_id}"
    task_queue = settings.temporal_task_queue

    if schedule_type == "interval":
        workflow = IntervalScheduleWorkflow
    elif schedule_type == "window":
        workflow = WindowScheduleWorkflow
    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")

    handle = await client.start_workflow(
        workflow.run,
        schedule_id,
        id=workflow_id,
        task_queue=task_queue,
    )

    return handle.id


async def terminate_schedule_workflow(
    schedule_id: UUID, client: Client | None = None
) -> None:
    if client is None:
        client = await get_temporal_client()

    workflow_id = f"schedule-{schedule_id}"
    handle = client.get_workflow_handle(workflow_id)

    await handle.terminate()


async def create_worker() -> Worker:
    client = await get_temporal_client()

    return Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[IntervalScheduleWorkflow, WindowScheduleWorkflow],
        activities=[
            get_schedule_and_target,
            execute_http_request,
            create_job_record,
        ],
    )

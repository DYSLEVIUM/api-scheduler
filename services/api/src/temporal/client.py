from uuid import UUID

from temporalio.client import Client
from temporalio.worker import Worker

from core.config import settings
from core.logging import get_logger
from temporal.activities import (create_job_record, execute_http_request,
                                 get_schedule_and_target)
from temporal.workflows import IntervalScheduleWorkflow, WindowScheduleWorkflow

logger = get_logger()


async def get_temporal_client() -> Client:
    logger.debug("temporal_client_connecting", host=settings.temporal_host, namespace=settings.temporal_namespace)
    client = await Client.connect(
        target_host=settings.temporal_host,
        namespace=settings.temporal_namespace,
    )
    logger.info("temporal_client_connected")
    return client


async def start_schedule_workflow(
    schedule_id: UUID, schedule_type: str, client: Client | None = None
) -> str:
    logger.info("temporal_workflow_starting", schedule_id=str(schedule_id), schedule_type=schedule_type)
    
    if client is None:
        client = await get_temporal_client()

    workflow_id = f"schedule-{schedule_id}"
    task_queue = settings.temporal_task_queue

    if schedule_type == "interval":
        workflow = IntervalScheduleWorkflow
    elif schedule_type == "window":
        workflow = WindowScheduleWorkflow
    else:
        logger.error("temporal_unknown_schedule_type", schedule_type=schedule_type)
        raise ValueError(f"Unknown schedule type: {schedule_type}")

    handle = await client.start_workflow(
        workflow.run,
        schedule_id,
        id=workflow_id,
        task_queue=task_queue,
    )

    logger.info("temporal_workflow_started", schedule_id=str(schedule_id), workflow_id=handle.id)
    return handle.id


async def terminate_schedule_workflow(
    schedule_id: UUID, client: Client | None = None
) -> None:
    logger.info("temporal_workflow_terminating", schedule_id=str(schedule_id))
    
    if client is None:
        client = await get_temporal_client()

    workflow_id = f"schedule-{schedule_id}"
    handle = client.get_workflow_handle(workflow_id)

    await handle.terminate()
    logger.info("temporal_workflow_terminated", schedule_id=str(schedule_id), workflow_id=workflow_id)


async def create_worker() -> Worker:
    import logging
    
    logger.info("temporal_worker_creating", task_queue=settings.temporal_task_queue)
    client = await get_temporal_client()

    workflow_logger = logging.getLogger("temporalio.workflow")
    workflow_logger.setLevel(logging.INFO)
    
    activity_logger = logging.getLogger("temporalio.activity")
    activity_logger.setLevel(logging.INFO)

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[IntervalScheduleWorkflow, WindowScheduleWorkflow],
        activities=[
            get_schedule_and_target,
            execute_http_request,
            create_job_record,
        ],
    )
    
    logger.info("temporal_worker_created")
    return worker

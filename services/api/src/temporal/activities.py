import asyncio
from datetime import UTC, datetime
from uuid import UUID

import httpx
from db.database import get_session
from db.models.job import Job as JobModel
from db.models.schedule import IntervalSchedule, WindowSchedule
from db.models.target import Target
from db.models.url import URL
from enums.http_methods import HTTPMethods
from enums.job_status import JobStatus
from models.job import Job as JobPydantic
from temporalio import activity


@activity.defn
async def get_schedule_and_target(schedule_id: UUID) -> dict:
    async with get_session() as session:
        from sqlmodel import select

        async def query_interval():
            result = await session.execute(
                select(IntervalSchedule).where(
                    IntervalSchedule.id == schedule_id)
            )
            return result.scalar_one_or_none()

        async def query_window():
            result = await session.execute(
                select(WindowSchedule).where(WindowSchedule.id == schedule_id)
            )
            return result.scalar_one_or_none()

        interval_schedule, window_schedule = await asyncio.gather(
            query_interval(), query_window()
        )

        schedule = interval_schedule or window_schedule
        if not schedule:
            return {"deleted": True}

        if schedule.paused:
            return {"paused": True}

        target_result = await session.execute(
            select(Target).where(Target.id == schedule.target_id)
        )
        target = target_result.scalar_one_or_none()
        if not target:
            raise ValueError(f"Target {schedule.target_id} not found")

        url_result = await session.execute(
            select(URL).where(URL.id == target.url_id)
        )
        url = url_result.scalar_one_or_none()
        if not url:
            raise ValueError(f"URL {target.url_id} not found")

        schedule_dict = {
            "interval_seconds": schedule.interval_seconds,
        }
        if hasattr(schedule, "duration_seconds"):
            schedule_dict["duration_seconds"] = schedule.duration_seconds

        return {
            "paused": False,
            "schedule": schedule_dict,
            "target": {
                "method": target.method.value,
                "headers": target.headers,
                "body": target.body,
            },
            "url": url.get_url_string(),
        }


@activity.defn
async def execute_http_request(
    url: str,
    method: str,
    headers: dict | None,
    body: dict | None,
    timeout_seconds: int = 30,
) -> dict:
    start_time = datetime.now(UTC)
    status = JobStatus.SUCCESS
    status_code = None
    latency_ms = None
    response_size_bytes = None
    response_headers = None
    response_body = None
    error_message = None

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            http_method = getattr(client, method.lower(), client.get)
            method_lower = method.lower()

            if method_lower in ("get", "head", "delete", "options"):
                kwargs = {"headers": headers or {}}
                if body:
                    kwargs["params"] = body
            else:
                kwargs = {"headers": headers or {}}
                if body:
                    kwargs["json"] = body

            response = await http_method(url, **kwargs)

            end_time = datetime.now(UTC)
            latency_ms = (end_time - start_time).total_seconds() * 1000
            status_code = response.status_code
            response_size_bytes = len(response.content)
            response_headers = dict(response.headers)
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            if status_code >= 500:
                status = JobStatus.HTTP_5XX
            elif status_code >= 400:
                status = JobStatus.HTTP_4XX

    except httpx.TimeoutException:
        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000
        status = JobStatus.TIMEOUT
        error_message = f"Request timed out after {timeout_seconds} seconds"
    except httpx.ConnectError as e:
        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000
        error_str = str(e).lower()
        if "name resolution" in error_str or "dns" in error_str or "getaddrinfo" in error_str:
            status = JobStatus.DNS_ERROR
        else:
            status = JobStatus.CONNECTION_ERROR
        error_message = f"Connection error: {str(e)}"
    except Exception as e:
        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000
        status = JobStatus.ERROR
        error_message = str(e)

    return {
        "status": status.value,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "response_size_bytes": response_size_bytes,
        "response_headers": response_headers,
        "response_body": response_body,
        "error_message": error_message,
        "started_at": start_time.replace(tzinfo=None),
    }


@activity.defn
async def create_job_record(
    schedule_id: UUID,
    run_number: int,
    request_result: dict,
) -> UUID:
    async with get_session() as session:
        started_at = request_result["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(
                started_at.replace("Z", "+00:00"))
            if started_at.tzinfo:
                started_at = started_at.replace(tzinfo=None)

        status = request_result["status"]
        if isinstance(status, JobStatus):
            status_value = status.value
        elif isinstance(status, str):
            status_lower = status.lower()
            try:
                status_enum = JobStatus(status_lower)
                status_value = status_enum.value
            except ValueError:
                status_value = JobStatus.ERROR.value
        else:
            status_value = JobStatus.ERROR.value

        job = JobModel(
            schedule_id=schedule_id,
            run_number=run_number,
            started_at=started_at,
            status=JobStatus(status_value),
            status_code=request_result.get("status_code"),
            latency_ms=request_result.get("latency_ms"),
            response_size_bytes=request_result.get("response_size_bytes"),
            response_headers=request_result.get("response_headers"),
            response_body=request_result.get("response_body"),
            error_message=request_result.get("error_message"),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job.id

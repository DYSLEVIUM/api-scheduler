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

        interval_result = await session.execute(
            select(IntervalSchedule).where(IntervalSchedule.id == schedule_id)
        )
        interval_schedule = interval_result.scalar_one_or_none()

        window_result = await session.execute(
            select(WindowSchedule).where(WindowSchedule.id == schedule_id)
        )
        window_schedule = window_result.scalar_one_or_none()

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
                "timeout_seconds": target.timeout_seconds,
                "retry_count": target.retry_count,
                "retry_delay_seconds": target.retry_delay_seconds,
                "follow_redirects": target.follow_redirects,
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
    retry_count: int = 0,
    retry_delay_seconds: int = 1,
    follow_redirects: bool = True,
) -> dict:
    import asyncio

    start_time = datetime.now(UTC)
    status = JobStatus.SUCCESS
    status_code = None
    latency_ms = None
    response_size_bytes = None
    response_headers = None
    response_body = None
    error_message = None
    last_exception = None
    redirect_history = []

    attempts = []

    for attempt in range(retry_count + 1):
        attempt_start = datetime.now(UTC)
        attempt_status = JobStatus.SUCCESS
        attempt_status_code = None
        attempt_latency = None
        attempt_size = None
        attempt_resp_headers = None
        attempt_resp_body = None
        attempt_error = None

        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                follow_redirects=follow_redirects,
            ) as client:
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

                # Track redirect history from response
                if hasattr(response, 'history') and response.history:
                    # follow_redirects=True: history contains intermediate redirects
                    for redirect_response in response.history:
                        redirect_history.append({
                            "url": str(redirect_response.url),
                            "status_code": redirect_response.status_code,
                        })
                elif response.is_redirect and not follow_redirects:
                    # follow_redirects=False: current response is the redirect
                    location = response.headers.get('location', '')
                    if location:
                        redirect_history.append({
                            "url": location,
                            "status_code": response.status_code,
                        })

                attempt_end = datetime.now(UTC)
                attempt_latency = (
                    attempt_end - attempt_start).total_seconds() * 1000
                attempt_status_code = response.status_code
                attempt_size = len(response.content)
                attempt_resp_headers = dict(response.headers)
                try:
                    attempt_resp_body = response.json()
                except Exception:
                    attempt_resp_body = response.text

                if attempt_status_code >= 500:
                    attempt_status = JobStatus.HTTP_5XX
                elif attempt_status_code >= 400:
                    attempt_status = JobStatus.HTTP_4XX

                status = attempt_status
                status_code = attempt_status_code
                latency_ms = (attempt_end - start_time).total_seconds() * 1000
                response_size_bytes = attempt_size
                response_headers = attempt_resp_headers
                response_body = attempt_resp_body

                attempts.append({
                    "attempt_number": attempt + 1,
                    "started_at": attempt_start.replace(tzinfo=None),
                    "status": attempt_status.value,
                    "status_code": attempt_status_code,
                    "latency_ms": attempt_latency,
                    "response_size_bytes": attempt_size,
                    "response_headers": attempt_resp_headers,
                    "response_body": attempt_resp_body,
                    "error_message": attempt_error,
                })

                if attempt_status_code >= 500 and attempt < retry_count:
                    await asyncio.sleep(retry_delay_seconds)
                    continue
                break

        except httpx.TimeoutException as e:
            last_exception = e
            attempt_end = datetime.now(UTC)
            attempt_latency = (
                attempt_end - attempt_start).total_seconds() * 1000
            attempt_status = JobStatus.TIMEOUT
            attempt_error = f"Request timed out after {timeout_seconds} seconds"

            attempts.append({
                "attempt_number": attempt + 1,
                "started_at": attempt_start.replace(tzinfo=None),
                "status": attempt_status.value,
                "status_code": None,
                "latency_ms": attempt_latency,
                "response_size_bytes": None,
                "response_headers": None,
                "response_body": None,
                "error_message": attempt_error,
            })

            if attempt < retry_count:
                await asyncio.sleep(retry_delay_seconds)
                continue
            status = attempt_status
            latency_ms = (attempt_end - start_time).total_seconds() * 1000
            error_message = attempt_error
            break

        except httpx.ConnectError as e:
            last_exception = e
            attempt_end = datetime.now(UTC)
            attempt_latency = (
                attempt_end - attempt_start).total_seconds() * 1000
            error_str = str(e).lower()
            dns_patterns = [
                "name resolution",
                "dns",
                "getaddrinfo",
                "name or service not known",
                "nodename nor servname",
            ]
            if any(pattern in error_str for pattern in dns_patterns):
                attempt_status = JobStatus.DNS_ERROR
                attempt_error = f"DNS resolution failed: {str(e)}"
            else:
                attempt_status = JobStatus.CONNECTION_ERROR
                attempt_error = f"Connection error: {str(e)}"

            attempts.append({
                "attempt_number": attempt + 1,
                "started_at": attempt_start.replace(tzinfo=None),
                "status": attempt_status.value,
                "status_code": None,
                "latency_ms": attempt_latency,
                "response_size_bytes": None,
                "response_headers": None,
                "response_body": None,
                "error_message": attempt_error,
            })

            if attempt < retry_count:
                await asyncio.sleep(retry_delay_seconds)
                continue
            status = attempt_status
            latency_ms = (attempt_end - start_time).total_seconds() * 1000
            error_message = attempt_error
            break

        except Exception as e:
            last_exception = e
            attempt_end = datetime.now(UTC)
            attempt_latency = (
                attempt_end - attempt_start).total_seconds() * 1000
            attempt_status = JobStatus.ERROR
            attempt_error = str(e)

            attempts.append({
                "attempt_number": attempt + 1,
                "started_at": attempt_start.replace(tzinfo=None),
                "status": attempt_status.value,
                "status_code": None,
                "latency_ms": attempt_latency,
                "response_size_bytes": None,
                "response_headers": None,
                "response_body": None,
                "error_message": attempt_error,
            })

            if attempt < retry_count:
                await asyncio.sleep(retry_delay_seconds)
                continue
            status = attempt_status
            latency_ms = (attempt_end - start_time).total_seconds() * 1000
            error_message = attempt_error
            break

    if last_exception and not error_message:
        error_message = str(last_exception)

    result = {
        "status": status.value,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "response_size_bytes": response_size_bytes,
        "response_headers": response_headers,
        "response_body": response_body,
        "error_message": error_message,
        "started_at": start_time.replace(tzinfo=None),
        "request_headers": headers,
        "request_body": body,
        "attempts": attempts,
    }

    # Add redirect information if any redirects occurred
    if redirect_history:
        result["redirect_history"] = redirect_history
        result["redirected"] = True
        result["redirect_count"] = len(redirect_history)
    else:
        result["redirected"] = False
        result["redirect_count"] = 0

    return result


@activity.defn
async def create_job_record(
    schedule_id: UUID,
    run_number: int,
    request_result: dict,
) -> UUID:
    from db.models.attempt import Attempt

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
            request_headers=request_result.get("request_headers"),
            request_body=request_result.get("request_body"),
            response_headers=request_result.get("response_headers"),
            response_body=request_result.get("response_body"),
            error_message=request_result.get("error_message"),
            redirected=request_result.get("redirected", False),
            redirect_count=request_result.get("redirect_count", 0),
            redirect_history=request_result.get("redirect_history"),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        attempts = request_result.get("attempts", [])
        for attempt_data in attempts:
            attempt_started_at = attempt_data["started_at"]
            if isinstance(attempt_started_at, str):
                attempt_started_at = datetime.fromisoformat(
                    attempt_started_at.replace("Z", "+00:00"))
                if attempt_started_at.tzinfo:
                    attempt_started_at = attempt_started_at.replace(
                        tzinfo=None)

            attempt_status = attempt_data["status"]
            if isinstance(attempt_status, str):
                try:
                    attempt_status = JobStatus(attempt_status.lower())
                except ValueError:
                    attempt_status = JobStatus.ERROR

            attempt = Attempt(
                job_id=job.id,
                attempt_number=attempt_data["attempt_number"],
                started_at=attempt_started_at,
                status=attempt_status,
                status_code=attempt_data.get("status_code"),
                latency_ms=attempt_data.get("latency_ms"),
                response_size_bytes=attempt_data.get("response_size_bytes"),
                response_headers=attempt_data.get("response_headers"),
                response_body=attempt_data.get("response_body"),
                error_message=attempt_data.get("error_message"),
            )
            session.add(attempt)

        await session.commit()
        return job.id

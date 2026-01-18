from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.job import Job as JobModel
from db.models.schedule import IntervalSchedule as IntervalScheduleModel
from db.models.target import Target as TargetModel
from db.models.url import URL as URLModel
from enums.http_methods import HTTPMethods
from enums.job_status import JobStatus


async def create_test_url(
    session: AsyncSession,
    scheme: str = "https",
    netloc: str = "api.example.com",
    path: str = "/v1/test",
    params: str | None = None,
    query: str | None = None,
    fragment: str | None = None,
) -> URLModel:
    url = URLModel(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params=params,
        query=query,
        fragment=fragment,
    )
    session.add(url)
    await session.commit()
    await session.refresh(url)
    return url


async def create_test_target(
    session: AsyncSession,
    url_id: UUID,
    name: str = "Test Target",
    method: HTTPMethods = HTTPMethods.GET,
    headers: dict | None = None,
    body: dict | None = None,
) -> TargetModel:
    target = TargetModel(
        name=name,
        url_id=url_id,
        method=method,
        headers=headers or {},
        body=body,
    )
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return target


async def create_test_schedule(
    session: AsyncSession,
    target_id: UUID,
    interval_seconds: int = 60,
    paused: bool = False,
    name: str = "Test Schedule",
) -> IntervalScheduleModel:
    schedule = IntervalScheduleModel(
        target_id=target_id,
        interval_seconds=interval_seconds,
        paused=paused,
        name=name,
    )
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return schedule


async def create_test_job(
    session: AsyncSession,
    schedule_id: UUID,
    run_number: int = 1,
    status: JobStatus = JobStatus.SUCCESS,
    status_code: int = 200,
    latency_ms: float | None = None,
    response_size_bytes: int | None = None,
) -> JobModel:
    job = JobModel(
        schedule_id=schedule_id,
        run_number=run_number,
        started_at=datetime.now(UTC),
        status=status,
        status_code=status_code,
        latency_ms=latency_ms,
        response_size_bytes=response_size_bytes,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def create_test_data_chain(
    session: AsyncSession,
    url_kwargs: dict | None = None,
    target_kwargs: dict | None = None,
    schedule_kwargs: dict | None = None,
) -> tuple[URLModel, TargetModel, IntervalScheduleModel]:
    url = await create_test_url(session, **(url_kwargs or {}))
    target = await create_test_target(
        session, url.id, **(target_kwargs or {})
    )
    schedule = await create_test_schedule(
        session, target.id, **(schedule_kwargs or {})
    )
    return url, target, schedule

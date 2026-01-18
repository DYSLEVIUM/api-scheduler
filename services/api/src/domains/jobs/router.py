from datetime import datetime
from typing import List
from uuid import UUID

from domains.jobs.schemas import JobResponse
from domains.jobs.service import JobService
from enums.job_status import JobStatus
from fastapi import APIRouter, HTTPException, Query, status
from models.response import HTTPResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])
service = JobService()


@router.get(
    "",
    response_model=HTTPResponse[List[JobResponse]],
    response_model_exclude_none=True,
    tags=["get all jobs"],
    status_code=status.HTTP_200_OK,
)
async def get_all_jobs(
    schedule_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
):
    try:
        status_enum = None
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
            except ValueError:
                pass

        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(
                    start_time.replace("Z", "+00:00"))
            except Exception:
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(
                    end_time.replace("Z", "+00:00"))
            except Exception:
                pass

        if schedule_id:
            job_pydantics = await service.get_jobs_by_schedule_id(
                schedule_id, status_enum, start_dt, end_dt
            )
        else:
            job_pydantics = await service.get_all_jobs(status_enum, start_dt, end_dt)
        job_responses = [j.to_response() for j in job_pydantics]
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Jobs retrieved successfully",
            data=job_responses,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{id}",
    response_model=HTTPResponse[JobResponse],
    response_model_exclude_none=True,
    tags=["get job by id"],
    status_code=status.HTTP_200_OK,
)
async def get_job_by_id(id: UUID):
    try:
        job_pydantic = await service.get_job_by_id(id)
        job_response = job_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Job retrieved successfully",
            data=job_response,
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

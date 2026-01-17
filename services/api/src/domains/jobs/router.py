from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from domains.jobs.schemas import JobResponse
from domains.jobs.service import JobService
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
async def get_all_jobs(schedule_id: UUID | None = Query(None)):
    try:
        if schedule_id:
            job_pydantics = await service.get_jobs_by_schedule_id(schedule_id)
        else:
            job_pydantics = await service.get_all_jobs()
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

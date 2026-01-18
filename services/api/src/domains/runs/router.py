from datetime import datetime
from typing import List
from uuid import UUID

from domains.runs.schemas import RunResponse
from domains.runs.service import RunService
from enums.job_status import JobStatus
from fastapi import APIRouter, HTTPException, Query, status
from models.response import HTTPResponse

router = APIRouter(prefix="/runs", tags=["runs"])
service = RunService()


@router.get(
    "",
    response_model=HTTPResponse[List[RunResponse]],
    response_model_exclude_none=True,
    tags=["get all runs"],
    status_code=status.HTTP_200_OK,
)
async def get_all_runs(
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
            run_pydantics = await service.get_runs_by_schedule_id(
                schedule_id, status_enum, start_dt, end_dt
            )
        else:
            run_pydantics = await service.get_all_runs(status_enum, start_dt, end_dt)
        run_responses = [RunResponse(**r.model_dump()) for r in run_pydantics]
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Runs retrieved successfully",
            data=run_responses,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{id}",
    response_model=HTTPResponse[RunResponse],
    response_model_exclude_none=True,
    tags=["get run by id"],
    status_code=status.HTTP_200_OK,
)
async def get_run_by_id(id: UUID):
    from domains.runs.schemas import AttemptResponse

    try:
        run_pydantic = await service.get_run_by_id(id)
        run_dict = run_pydantic.model_dump()

        if run_dict.get("attempts"):
            run_dict["attempts"] = [
                AttemptResponse(**attempt) if isinstance(attempt, dict)
                else AttemptResponse(**attempt.model_dump())
                for attempt in run_dict["attempts"]
            ]

        run_response = RunResponse(**run_dict)
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Run retrieved successfully",
            data=run_response,
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

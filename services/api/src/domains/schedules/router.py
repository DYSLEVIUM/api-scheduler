from __future__ import annotations

from typing import List
from uuid import UUID

from core.decorators import log
from fastapi import APIRouter, HTTPException, status

from domains.schedules.schemas import ScheduleRequest, ScheduleResponse
from domains.schedules.service import ScheduleService
from models.response import HTTPResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])
service = ScheduleService()


@router.post(
    "",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["create schedule"],
    status_code=status.HTTP_201_CREATED,
)
@log(operation_name="api.POST /schedules", log_args=False)
async def create_schedule(schedule: ScheduleRequest):
    try:
        schedule_model = schedule.to_model()
        schedule_pydantic = await service.create_schedule(schedule_model)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_201_CREATED,
            message="Schedule created successfully",
            data=schedule_response,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "",
    response_model=HTTPResponse[List[ScheduleResponse]],
    response_model_exclude_none=True,
    tags=["get all schedules"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.GET /schedules")
async def get_all_schedules():
    try:
        schedule_pydantics = await service.get_all_schedules()
        schedule_responses = [s.to_response() for s in schedule_pydantics]
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedules retrieved successfully",
            data=schedule_responses,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{id}",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["get schedule by id"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.GET /schedules/{id}", log_args=False)
async def get_schedule_by_id(id: UUID):
    try:
        schedule_pydantic = await service.get_schedule_by_id(id)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedule retrieved successfully",
            data=schedule_response,
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


@router.post(
    "/{id}/pause",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["pause schedule"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.POST /schedules/{id}/pause", log_args=False)
async def pause_schedule(id: UUID):
    try:
        schedule_pydantic = await service.pause_schedule(id)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedule paused successfully",
            data=schedule_response,
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


@router.post(
    "/{id}/resume",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["resume schedule"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.POST /schedules/{id}/resume", log_args=False)
async def resume_schedule(id: UUID):
    try:
        schedule_pydantic = await service.resume_schedule(id)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedule resumed successfully",
            data=schedule_response,
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


@router.put(
    "/{id}",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["update schedule"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.PUT /schedules/{id}", log_args=False)
async def update_schedule(id: UUID, schedule: ScheduleRequest):
    try:
        schedule_model = schedule.to_model()
        schedule_pydantic = await service.update_schedule(id, schedule_model)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedule updated successfully",
            data=schedule_response,
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


@router.delete(
    "/{id}",
    response_model=HTTPResponse[ScheduleResponse],
    response_model_exclude_none=True,
    tags=["delete schedule"],
    status_code=status.HTTP_200_OK,
)
@log(operation_name="api.DELETE /schedules/{id}", log_args=False)
async def delete_schedule(id: UUID):
    try:
        schedule_pydantic = await service.delete_schedule(id)
        schedule_response = schedule_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Schedule deleted successfully",
            data=schedule_response,
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

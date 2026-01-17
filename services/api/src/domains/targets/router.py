from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from models.response import HTTPResponse

from .schemas import TargetRequest, TargetResponse
from .service import TargetService

router = APIRouter(prefix="/targets")
service = TargetService()


@router.get(
    "/{target_id}",
    response_model=HTTPResponse[TargetResponse],
    tags=["get target by id"],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def get_target_by_id(target_id: UUID):
    try:
        target_pydantic = await service.get_target_by_id(target_id)
        target_response = target_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Target retrieved successfully",
            data=target_response,
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "database error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "",
    response_model=HTTPResponse[List[TargetResponse]],
    tags=["get all targets"],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def get_all_targets():
    try:
        target_pydantics = await service.get_all_targets()
        target_responses = [t.to_response() for t in target_pydantics]
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Targets retrieved successfully",
            data=target_responses,
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "database error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "",
    response_model=HTTPResponse[TargetResponse],
    tags=["create target"],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_target(target: TargetRequest):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"Creating target with data: {target.model_dump(exclude={'id', 'created_at', 'updated_at'})}")
        target_model = target.to_model()
        target_pydantic = await service.create_target(target_model)
        target_response = target_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_201_CREATED,
            message="Target created successfully",
            data=target_response,
        )
    except ValueError as e:
        logger.warning(f"Validation error in create_target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in create_target: {type(e).__name__}: {str(e)}", exc_info=True)
        error_msg = str(e).lower()
        if "database error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/{target_id}",
    response_model=HTTPResponse[TargetResponse],
    tags=["update target"],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def update_target(target_id: UUID, target: TargetRequest):
    try:
        target_model = target.to_model()
        target_pydantic = await service.update_target(target_id, target_model)
        target_response = target_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Target updated successfully",
            data=target_response,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "database error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{target_id}",
    response_model=HTTPResponse[TargetResponse],
    tags=["delete target"],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def delete_target(target_id: UUID):
    try:
        target_pydantic = await service.delete_target(target_id)
        target_response = target_pydantic.to_response()
        return HTTPResponse(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Target deleted successfully",
            data=target_response,
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "database error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

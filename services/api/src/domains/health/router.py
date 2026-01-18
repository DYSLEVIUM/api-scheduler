from core.logging import get_logger
from core.metrics import get_metrics_response
from fastapi import APIRouter, status
from models.response import HTTPResponse

from .schemas import HealthResponse

router = APIRouter(prefix="/health")


@router.get(
    "/",
    response_model=HTTPResponse[HealthResponse],
    tags=["health"],
    response_model_exclude_none=True,
)
async def health():
    logger = get_logger()
    logger.debug("health_check_requested")

    return HTTPResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Health check successful",
    )


@router.get("/metrics", tags=["metrics"])
async def metrics():
    return get_metrics_response()

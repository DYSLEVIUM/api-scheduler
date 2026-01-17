from fastapi import APIRouter, status
from models.response import HTTPResponse

from core.metrics import get_metrics_response

from .schemas import HealthResponse

router = APIRouter(prefix="/health")


@router.get(
    "/",
    response_model=HTTPResponse[HealthResponse],
    tags=["health"],
    response_model_exclude_none=True,
)
async def health():
    return HTTPResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Health check successful",
    )


@router.get("/metrics", tags=["metrics"])
async def metrics():
    return get_metrics_response()

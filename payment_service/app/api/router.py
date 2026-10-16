from fastapi import APIRouter, Depends

from app.api.v1.routers.payments import payments
from app.utils.utils import validate_api_key

api_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(validate_api_key)],
)
api_router.include_router(payments)
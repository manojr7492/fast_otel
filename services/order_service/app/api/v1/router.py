from fastapi import APIRouter
from app.api.v1.endpoints.orders import router as orders_router

api_v1_router = APIRouter()
api_v1_router.include_router(
    orders_router, prefix="/orders", tags=["Orders"]
)


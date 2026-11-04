from fastapi import APIRouter
from app.api.v1.endpoints.payments import router as payments_router

api_v1_router = APIRouter()
api_v1_router.include_router(
    payments_router, prefix="/payments", tags=["Payments"]
)


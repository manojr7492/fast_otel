from fastapi import APIRouter
from app.api.v1.endpoints.notifications import router as notifications_router

api_v1_router = APIRouter()
api_v1_router.include_router(
    notifications_router, prefix="/notifications", tags=["Notifications"]
)


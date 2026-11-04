from fastapi import APIRouter
from app.api.v1.endpoints.inventory import router as inventory_router

api_v1_router = APIRouter()
api_v1_router.include_router(
    inventory_router, prefix="/inventory", tags=["Inventory"]
)


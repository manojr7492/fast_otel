from fastapi import APIRouter
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.products import router as products_router

api_v1_router = APIRouter()
api_v1_router.include_router(
    categories_router, prefix="/categories", tags=["Categories"]
)
api_v1_router.include_router(
    products_router, prefix="/products", tags=["Products"]
)


from typing import List
from fastapi import APIRouter, Depends, status

from app.api.deps import get_catalog_service
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.common import APIResponse
from app.services.product_service import ProductCatalogService

router = APIRouter()


@router.get(
    "/",
    response_model=APIResponse[List[CategoryResponse]],
    summary="List all product categories",
)
async def list_categories(
    service: ProductCatalogService = Depends(get_catalog_service),
):
    categories = await service.list_categories()
    return APIResponse(
        success=True,
        status_code=200,
        message="Categories retrieved successfully.",
        data=categories,
    )


@router.post(
    "/",
    response_model=APIResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product category",
)
async def create_category(
    payload: CategoryCreate,
    service: ProductCatalogService = Depends(get_catalog_service),
):
    category = await service.create_category(payload)
    return APIResponse(
        success=True,
        status_code=201,
        message="Category created successfully.",
        data=category,
    )


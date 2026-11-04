from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_catalog_service
from app.schemas.common import APIResponse, PaginatedData, PaginationParams
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductCatalogService

router = APIRouter()


@router.get(
    "/",
    response_model=APIResponse[PaginatedData[ProductResponse]],
    summary="List products with filtering and pagination",
)
async def list_products(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    category_uuid: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=True),
    search: Optional[str] = Query(default=None),
    service: ProductCatalogService = Depends(get_catalog_service),
):
    pagination = PaginationParams(page=page, size=size)
    data = await service.list_products(
        pagination=pagination,
        category_uuid=category_uuid,
        is_active=is_active,
        search_query=search,
    )
    return APIResponse(
        success=True,
        status_code=200,
        message="Products retrieved successfully.",
        data=data,
    )


@router.post(
    "/",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new catalog product",
)
async def create_product(
    payload: ProductCreate,
    service: ProductCatalogService = Depends(get_catalog_service),
):
    product = await service.create_product(payload)
    return APIResponse(
        success=True,
        status_code=201,
        message="Product created successfully.",
        data=product,
    )


@router.get(
    "/{identifier}",
    response_model=APIResponse[ProductResponse],
    summary="Get product details by UUID or SKU",
)
async def get_product(
    identifier: str,
    service: ProductCatalogService = Depends(get_catalog_service),
):
    product = await service.get_product(identifier)
    return APIResponse(
        success=True,
        status_code=200,
        message="Product retrieved successfully.",
        data=product,
    )


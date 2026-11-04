from fastapi import APIRouter, Depends, status

from app.api.deps import get_inventory_service
from app.schemas.common import APIResponse
from app.schemas.inventory import (
    CommitStockRequest,
    ReleaseStockRequest,
    ReservationResponse,
    ReserveStockRequest,
    RestockRequest,
    StockCheckResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get(
    "/{sku}",
    response_model=APIResponse[StockCheckResponse],
    summary="Check available inventory for a SKU",
)
async def check_stock(
    sku: str,
    service: InventoryService = Depends(get_inventory_service),
):
    stock = await service.get_stock(sku)
    return APIResponse(
        success=True,
        status_code=200,
        message=f"Stock info for SKU '{sku}' retrieved.",
        data=stock,
    )


@router.post(
    "/restock",
    response_model=APIResponse[StockCheckResponse],
    summary="Add stock to inventory",
)
async def restock_item(
    payload: RestockRequest,
    service: InventoryService = Depends(get_inventory_service),
):
    updated = await service.restock(payload)
    return APIResponse(
        success=True,
        status_code=200,
        message=f"Successfully added {payload.quantity} units to SKU '{payload.sku}'.",
        data=updated,
    )


@router.post(
    "/reserve",
    response_model=APIResponse[ReservationResponse],
    status_code=status.HTTP_200_OK,
    summary="Reserve stock for an order",
)
async def reserve_stock(
    payload: ReserveStockRequest,
    service: InventoryService = Depends(get_inventory_service),
):
    reservation = await service.reserve_stock(payload)
    return APIResponse(
        success=True,
        status_code=200,
        message="Inventory reserved successfully.",
        data=reservation,
    )


@router.post(
    "/commit",
    response_model=APIResponse[dict],
    summary="Commit reserved stock upon payment success",
)
async def commit_stock(
    payload: CommitStockRequest,
    service: InventoryService = Depends(get_inventory_service),
):
    await service.commit_stock(payload)
    return APIResponse(
        success=True,
        status_code=200,
        message=f"Stock committed for order '{payload.order_uuid}'.",
        data={"order_uuid": payload.order_uuid, "status": "COMMITTED"},
    )


@router.post(
    "/release",
    response_model=APIResponse[dict],
    summary="Release reserved stock on order cancel or payment failure",
)
async def release_stock(
    payload: ReleaseStockRequest,
    service: InventoryService = Depends(get_inventory_service),
):
    await service.release_stock(payload)
    return APIResponse(
        success=True,
        status_code=200,
        message=f"Stock released for order '{payload.order_uuid}'.",
        data={"order_uuid": payload.order_uuid, "status": "RELEASED"},
    )


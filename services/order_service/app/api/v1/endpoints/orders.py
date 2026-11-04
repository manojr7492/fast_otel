from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_order_service
from app.models.order import OrderStatus
from app.schemas.common import APIResponse, PaginatedData, PaginationParams
from app.schemas.order import OrderCheckoutRequest, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()


@router.post(
    "/checkout",
    response_model=APIResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Order Checkout (Cross-Service Distributed Saga)",
)
async def checkout_order(
    payload: OrderCheckoutRequest,
    service: OrderService = Depends(get_order_service),
):
    order = await service.checkout(payload)
    return APIResponse(
        success=True,
        status_code=201,
        message="Order placed and confirmed successfully.",
        data=order,
    )


@router.get(
    "/{order_uuid}",
    response_model=APIResponse[OrderResponse],
    summary="Get order details by UUID",
)
async def get_order(
    order_uuid: str,
    service: OrderService = Depends(get_order_service),
):
    order = await service.get_order(order_uuid)
    return APIResponse(
        success=True,
        status_code=200,
        message="Order retrieved successfully.",
        data=order,
    )


@router.get(
    "/",
    response_model=APIResponse[PaginatedData[OrderResponse]],
    summary="List orders with pagination and filtering",
)
async def list_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user_uuid: Optional[str] = Query(default=None),
    status: Optional[OrderStatus] = Query(default=None),
    service: OrderService = Depends(get_order_service),
):
    pagination = PaginationParams(page=page, size=size)
    orders = await service.list_orders(
        pagination=pagination,
        user_uuid=user_uuid,
        status=status,
    )
    return APIResponse(
        success=True,
        status_code=200,
        message="Orders retrieved successfully.",
        data=orders,
    )


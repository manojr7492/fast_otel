from fastapi import APIRouter, Depends, status

from app.api.deps import get_payment_service
from app.schemas.common import APIResponse
from app.schemas.payment import (
    PaymentResponse,
    ProcessPaymentRequest,
    RefundPaymentRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post(
    "/process",
    response_model=APIResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Process payment transaction for an order",
)
async def process_payment(
    payload: ProcessPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.process_payment(payload)
    return APIResponse(
        success=True,
        status_code=200,
        message="Payment processed successfully.",
        data=payment,
    )


@router.get(
    "/{identifier}",
    response_model=APIResponse[PaymentResponse],
    summary="Get payment details by payment UUID or order UUID",
)
async def get_payment(
    identifier: str,
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.get_payment(identifier)
    return APIResponse(
        success=True,
        status_code=200,
        message="Payment retrieved successfully.",
        data=payment,
    )


@router.post(
    "/{payment_uuid}/refund",
    response_model=APIResponse[PaymentResponse],
    summary="Refund a completed payment transaction",
)
async def refund_payment(
    payment_uuid: str,
    payload: RefundPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
):
    refunded = await service.refund_payment(payment_uuid, payload)
    return APIResponse(
        success=True,
        status_code=200,
        message="Payment refunded successfully.",
        data=refunded,
    )


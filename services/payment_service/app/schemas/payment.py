from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod, PaymentStatus


class ProcessPaymentRequest(BaseModel):
    order_uuid: str = Field(..., description="Target order UUID")
    user_uuid: str = Field(..., description="Purchaser user UUID")
    amount: Decimal = Field(..., gt=0, description="Total amount to be charged")
    currency: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CREDIT_CARD)
    simulate_failure: Optional[bool] = Field(
        default=False, description="Set to True for testing failed payment flows"
    )


class RefundPaymentRequest(BaseModel):
    reason: Optional[str] = "Customer requested refund"


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    order_uuid: str
    user_uuid: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    provider: str
    status: PaymentStatus
    transaction_reference: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


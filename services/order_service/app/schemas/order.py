from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_uuid: str = Field(..., description="UUID of catalog product")
    sku: str = Field(..., description="SKU identifier")
    quantity: int = Field(..., gt=0, description="Quantity to purchase")


class OrderCheckoutRequest(BaseModel):
    user_uuid: str = Field(..., description="UUID of authenticated purchaser")
    customer_email: str = Field(..., description="Email for order confirmation notification")
    customer_name: Optional[str] = "Valued Customer"
    shipping_address_uuid: Optional[str] = Field(None, description="UUID of shipping address")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Order line items")
    payment_method: str = Field(default="CREDIT_CARD", description="CREDIT_CARD, DEBIT_CARD, UPI, etc.")
    simulate_payment_failure: Optional[bool] = Field(
        default=False, description="Set True to test payment failure & compensation saga"
    )


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    product_uuid: str
    sku: str
    product_name: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    user_uuid: str
    status: OrderStatus
    total_amount: Decimal
    currency: str
    shipping_address_uuid: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime


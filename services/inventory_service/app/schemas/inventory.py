from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StockCheckResponse(BaseModel):
    sku: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    in_stock: bool


class RestockRequest(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    quantity: int = Field(..., gt=0)
    warehouse_location: Optional[str] = "WAREHOUSE-MAIN"


class ReserveItemRequest(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)


class ReserveStockRequest(BaseModel):
    order_uuid: str
    items: List[ReserveItemRequest]


class ReservationResponse(BaseModel):
    order_uuid: str
    status: str
    reserved_items: List[ReserveItemRequest]
    message: str


class ReleaseStockRequest(BaseModel):
    order_uuid: str


class CommitStockRequest(BaseModel):
    order_uuid: str


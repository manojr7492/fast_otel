from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=220)
    sku: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    is_active: bool = True


class ProductCreate(ProductBase):
    category_uuid: str


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    slug: Optional[str] = Field(None, min_length=2, max_length=220)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None
    category_uuid: Optional[str] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    category_id: int
    created_at: datetime
    updated_at: datetime


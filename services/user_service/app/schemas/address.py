from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.address import AddressType


class AddressBase(BaseModel):
    address_type: AddressType = Field(default=AddressType.SHIPPING)
    street_address: str = Field(..., min_length=3, max_length=255)
    apartment: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = Field(default="India", min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    is_default: bool = Field(default=False)


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_type: Optional[AddressType] = None
    street_address: Optional[str] = Field(None, min_length=3, max_length=255)
    apartment: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    uuid: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

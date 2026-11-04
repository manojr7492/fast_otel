import enum
import uuid
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class AddressType(str, enum.Enum):
    SHIPPING = "SHIPPING"
    BILLING = "BILLING"


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    address_type: Mapped[AddressType] = mapped_column(
        Enum(AddressType, name="address_type_enum"),
        default=AddressType.SHIPPING,
        nullable=False,
    )
    street_address: Mapped[str] = mapped_column(String(255), nullable=False)
    apartment: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="addresses")

    __table_args__ = (
        Index("ix_addresses_user_default", "user_id", "is_default"),
    )

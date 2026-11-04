import uuid
from typing import Optional
from sqlalchemy import BigInteger, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warehouse_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity - self.reserved_quantity)


class StockReservation(Base, TimestampMixin):
    __tablename__ = "stock_reservations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_uuid: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True, nullable=False)

    __table_args__ = (
        Index("ix_reservations_order_sku", "order_uuid", "sku"),
    )


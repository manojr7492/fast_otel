from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, InsufficientStockException
from app.core.telemetry import get_tracer
from app.models.inventory import InventoryItem
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.inventory import (
    CommitStockRequest,
    ReleaseStockRequest,
    ReservationResponse,
    ReserveItemRequest,
    ReserveStockRequest,
    RestockRequest,
    StockCheckResponse,
)

tracer = get_tracer("inventory_service")


class InventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = InventoryRepository(session)

    async def get_stock(self, sku: str) -> StockCheckResponse:
        with tracer.start_as_current_span("inventory.check_stock") as span:
            span.set_attribute("inventory.sku", sku)
            item = await self.repo.get_by_sku(sku)
            if not item:
                # Return 0 available if item is uninitialized
                return StockCheckResponse(
                    sku=sku,
                    quantity=0,
                    reserved_quantity=0,
                    available_quantity=0,
                    in_stock=False,
                )

            avail = item.available_quantity
            span.set_attribute("inventory.available_quantity", avail)
            return StockCheckResponse(
                sku=sku,
                quantity=item.quantity,
                reserved_quantity=item.reserved_quantity,
                available_quantity=avail,
                in_stock=avail > 0,
            )

    async def restock(self, restock_in: RestockRequest) -> StockCheckResponse:
        with tracer.start_as_current_span("inventory.restock") as span:
            span.set_attribute("inventory.sku", restock_in.sku)
            span.set_attribute("inventory.added_quantity", restock_in.quantity)

            item = await self.repo.get_by_sku(restock_in.sku)
            if not item:
                item = InventoryItem(
                    sku=restock_in.sku.strip().upper(),
                    quantity=restock_in.quantity,
                    reserved_quantity=0,
                    warehouse_location=restock_in.warehouse_location,
                )
                await self.repo.create(item)
            else:
                item.quantity += restock_in.quantity

            await self.session.commit()
            await self.session.refresh(item)
            return StockCheckResponse(
                sku=item.sku,
                quantity=item.quantity,
                reserved_quantity=item.reserved_quantity,
                available_quantity=item.available_quantity,
                in_stock=item.available_quantity > 0,
            )

    async def reserve_stock(self, reserve_in: ReserveStockRequest) -> ReservationResponse:
        with tracer.start_as_current_span("inventory.reserve_stock") as span:
            span.set_attribute("order.uuid", reserve_in.order_uuid)
            span.set_attribute("items.count", len(reserve_in.items))

            # 1. Verify availability for all requested items
            items_to_reserve = []
            for req_item in reserve_in.items:
                inv_item = await self.repo.get_by_sku(req_item.sku)
                if not inv_item:
                    raise EntityNotFoundException("InventoryItem", req_item.sku)

                if inv_item.available_quantity < req_item.quantity:
                    span.set_attribute("inventory.error", "insufficient_stock")
                    raise InsufficientStockException(
                        sku=req_item.sku,
                        requested=req_item.quantity,
                        available=inv_item.available_quantity,
                    )
                items_to_reserve.append((inv_item, req_item.quantity))

            # 2. Atomically reserve
            for inv_item, qty in items_to_reserve:
                inv_item.reserved_quantity += qty
                await self.repo.create_reservation(
                    order_uuid=reserve_in.order_uuid,
                    sku=inv_item.sku,
                    quantity=qty,
                )

            await self.session.commit()
            span.set_attribute("reservation.status", "RESERVED")
            return ReservationResponse(
                order_uuid=reserve_in.order_uuid,
                status="RESERVED",
                reserved_items=reserve_in.items,
                message="Inventory stock reserved successfully for order checkout.",
            )

    async def commit_stock(self, commit_in: CommitStockRequest) -> None:
        with tracer.start_as_current_span("inventory.commit_stock") as span:
            span.set_attribute("order.uuid", commit_in.order_uuid)
            reservations = await self.repo.get_reservations_by_order(commit_in.order_uuid)

            for res in reservations:
                inv_item = await self.repo.get_by_sku(res.sku)
                if inv_item:
                    inv_item.quantity = max(0, inv_item.quantity - res.quantity)
                    inv_item.reserved_quantity = max(0, inv_item.reserved_quantity - res.quantity)
                res.status = "COMMITTED"

            await self.session.commit()
            span.set_attribute("inventory.committed_count", len(reservations))

    async def release_stock(self, release_in: ReleaseStockRequest) -> None:
        with tracer.start_as_current_span("inventory.release_stock") as span:
            span.set_attribute("order.uuid", release_in.order_uuid)
            reservations = await self.repo.get_reservations_by_order(release_in.order_uuid)

            for res in reservations:
                inv_item = await self.repo.get_by_sku(res.sku)
                if inv_item:
                    inv_item.reserved_quantity = max(0, inv_item.reserved_quantity - res.quantity)
                res.status = "RELEASED"

            await self.session.commit()
            span.set_attribute("inventory.released_count", len(reservations))


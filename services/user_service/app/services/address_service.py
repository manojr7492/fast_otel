from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.telemetry import get_tracer
from app.models.address import Address
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate

tracer = get_tracer("address_service")


class AddressService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.address_repo = AddressRepository(session)

    async def list_user_addresses(self, user: User) -> List[AddressResponse]:
        with tracer.start_as_current_span("address.list_by_user") as span:
            span.set_attribute("user.id", user.id)
            addresses = await self.address_repo.list_by_user_id(user.id)
            span.set_attribute("address.count", len(addresses))
            return [AddressResponse.model_validate(addr) for addr in addresses]

    async def get_user_address(self, user: User, address_uuid: str) -> AddressResponse:
        with tracer.start_as_current_span("address.get_by_uuid") as span:
            span.set_attribute("user.id", user.id)
            span.set_attribute("address.uuid", address_uuid)
            address = await self.address_repo.get_by_uuid_and_user_id(
                address_uuid, user.id
            )
            if not address:
                raise EntityNotFoundException("Address", address_uuid)
            return AddressResponse.model_validate(address)

    async def create_user_address(
        self, user: User, create_in: AddressCreate
    ) -> AddressResponse:
        with tracer.start_as_current_span("address.create") as span:
            span.set_attribute("user.id", user.id)
            span.set_attribute("address.type", create_in.address_type.value)
            span.set_attribute("address.is_default", create_in.is_default)

            # If user sets this as default, unset previous default addresses
            if create_in.is_default:
                with tracer.start_as_current_span("address.reset_default_addresses"):
                    await self.address_repo.reset_default_addresses(user.id)

            new_address = Address(
                user_id=user.id,
                address_type=create_in.address_type,
                street_address=create_in.street_address,
                apartment=create_in.apartment,
                city=create_in.city,
                state=create_in.state,
                country=create_in.country,
                postal_code=create_in.postal_code,
                is_default=create_in.is_default,
            )

            address = await self.address_repo.create(new_address)
            await self.session.commit()
            await self.session.refresh(address)

            span.set_attribute("address.uuid", address.uuid)
            return AddressResponse.model_validate(address)

    async def update_user_address(
        self, user: User, address_uuid: str, update_in: AddressUpdate
    ) -> AddressResponse:
        with tracer.start_as_current_span("address.update") as span:
            span.set_attribute("user.id", user.id)
            span.set_attribute("address.uuid", address_uuid)

            address = await self.address_repo.get_by_uuid_and_user_id(
                address_uuid, user.id
            )
            if not address:
                raise EntityNotFoundException("Address", address_uuid)

            update_data = update_in.model_dump(exclude_unset=True)

            if update_data.get("is_default") is True and not address.is_default:
                with tracer.start_as_current_span("address.reset_default_addresses"):
                    await self.address_repo.reset_default_addresses(user.id)

            for key, value in update_data.items():
                setattr(address, key, value)

            await self.address_repo.update(address)
            await self.session.commit()
            await self.session.refresh(address)
            return AddressResponse.model_validate(address)

    async def delete_user_address(self, user: User, address_uuid: str) -> None:
        with tracer.start_as_current_span("address.delete") as span:
            span.set_attribute("user.id", user.id)
            span.set_attribute("address.uuid", address_uuid)

            address = await self.address_repo.get_by_uuid_and_user_id(
                address_uuid, user.id
            )
            if not address:
                raise EntityNotFoundException("Address", address_uuid)

            await self.address_repo.delete(address)
            await self.session.commit()

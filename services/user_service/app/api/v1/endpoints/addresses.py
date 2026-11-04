from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.schemas.common import APIResponse
from app.services.address_service import AddressService

router = APIRouter()


@router.get(
    "/",
    response_model=APIResponse[List[AddressResponse]],
    summary="List all addresses of current user",
)
async def list_addresses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AddressService(db)
    addresses = await service.list_user_addresses(current_user)
    return APIResponse(
        message="Addresses retrieved successfully.",
        data=addresses,
    )


@router.post(
    "/",
    response_model=APIResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new shipping or billing address",
)
async def create_address(
    create_in: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AddressService(db)
    new_address = await service.create_user_address(current_user, create_in)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Address created successfully.",
        data=new_address,
    )


@router.get(
    "/{uuid}",
    response_model=APIResponse[AddressResponse],
    summary="Get single address details",
)
async def get_address(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AddressService(db)
    address = await service.get_user_address(current_user, uuid)
    return APIResponse(
        message="Address retrieved successfully.",
        data=address,
    )


@router.put(
    "/{uuid}",
    response_model=APIResponse[AddressResponse],
    summary="Update an existing address",
)
async def update_address(
    uuid: str,
    update_in: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AddressService(db)
    updated = await service.update_user_address(current_user, uuid, update_in)
    return APIResponse(
        message="Address updated successfully.",
        data=updated,
    )


@router.delete(
    "/{uuid}",
    response_model=APIResponse[dict],
    summary="Delete an address",
)
async def delete_address(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AddressService(db)
    await service.delete_user_address(current_user, uuid)
    return APIResponse(
        message="Address deleted successfully.",
        data={"deleted": True, "uuid": uuid},
    )

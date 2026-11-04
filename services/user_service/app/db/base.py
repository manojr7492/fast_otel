# Import all the models, so that Base has them before being
# imported by Alembic
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.address import Address, AddressType

__all__ = ["Base", "User", "UserRole", "Address", "AddressType"]

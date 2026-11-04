from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting from 1")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    total_records: int
    current_page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMeta


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    status_code: int = 200
    message: str = "Operation completed successfully."
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = Field(
        default_factory=lambda: {"timestamp": datetime.now(timezone.utc).isoformat()}
    )

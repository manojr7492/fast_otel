from datetime import datetime, timezone
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    status_code: int = 200
    message: str = "Operation completed successfully."
    data: Optional[T] = None
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.now(timezone.utc).isoformat()}
    )


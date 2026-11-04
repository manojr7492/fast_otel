from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=404,
            error_code=f"{entity_name.upper()}_NOT_FOUND",
        )


class InsufficientStockException(AppException):
    def __init__(self, sku: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient inventory for SKU '{sku}'. Requested: {requested}, Available: {available}.",
            status_code=409,
            error_code="INSUFFICIENT_STOCK",
            details={"sku": sku, "requested": requested, "available": available},
        )


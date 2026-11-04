from typing import Any, Optional


class AppException(Exception):
    """Base application exception for domain errors."""

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
            error_code="ENTITY_NOT_FOUND",
            details={"entity": entity_name, "identifier": str(identifier)},
        )


class EntityAlreadyExistsException(AppException):
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            message=f"{entity_name} with {field} '{value}' already exists.",
            status_code=409,
            error_code="ENTITY_ALREADY_EXISTS",
            details={"entity": entity_name, "field": field, "value": str(value)},
        )


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Invalid email/username or password."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="INVALID_CREDENTIALS",
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required to access this resource."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class UserInactiveException(AppException):
    def __init__(self, message: str = "This user account is inactive or suspended."):
        super().__init__(
            message=message,
            status_code=403,
            error_code="USER_INACTIVE",
        )


class TokenExpiredException(AppException):
    def __init__(self, message: str = "Authentication token has expired."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_EXPIRED",
        )


class TokenInvalidException(AppException):
    def __init__(self, message: str = "Invalid or malformed authentication token."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_INVALID",
        )


class BadRequestException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
            details=details,
        )

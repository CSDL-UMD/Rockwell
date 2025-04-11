from fastapi import status

class AppException(Exception):
    """Base application exception class."""
    
    def __init__(
        self, 
        detail: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "internal_error"
    ):
        self.detail = detail
        self.status_code = status_code
        self.code = code


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="authentication_error"
        )


class AuthorizationError(AppException):
    """Raised when a user doesn't have permission."""
    
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            code="authorization_error"
        )


class NotFoundError(AppException):
    """Raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found"
        )


class ValidationError(AppException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error"
        )
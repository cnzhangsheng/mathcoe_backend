"""
Custom exceptions for the application
"""
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception"""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
        headers: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UnauthorizedException(AppException):
    """Unauthorized access exception"""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class WeChatAuthException(AppException):
    """WeChat authentication failed"""

    def __init__(self, detail: str = "WeChat authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
import structlog
from fastapi import status, FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger("app.exception")

class AppException(Exception):
    """
    Base Exception for all exceptions in the application.
    """

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DomainException(AppException):
    """
    Exception for business rule violations.
    """
    pass


class AuthenticationError(AppException):
    """
    Exception for failed authentication attempts.
    """

    def __init__(self, message: str = "Invalid or expired credentials"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class RateLimitExceeded(AppException):
    """
    Exception for rate limit exceeded.
    """
    def __init__(
        self, message: str = "Too many requests. Please try again later."
    ):
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)



class AppExceptionHandler:
    """
    Class-based exception handler manager.
    """

    def __init__(self, app: FastAPI):
        self.app = app

    def register(self) -> None:
        """Register all application exception handlers."""
        self.app.add_exception_handler(AppException, self.handle_app_exception)

    async def handle_app_exception(
        self, request: Request, exc: AppException
    ) -> JSONResponse:
        logger.warning(
            "app_exception",
            path=request.url.path,
            status_code=exc.status_code,
            message=exc.message,
            exception_class=exc.__class__.__name__,
        )
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.message}
        )

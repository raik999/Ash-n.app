import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ashun")


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "Ocurrio un error"

    def __init__(self, message: str | None = None, *, field: str | None = None):
        self.message = message or self.default_message
        self.field = field
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Recurso no encontrado"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "El recurso ya existe"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Credenciales invalidas"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "No tienes permiso para realizar esta accion"


class ValidationError(AppError):
    status_code = 422
    default_message = "Datos invalidos"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        body: dict = {"detail": exc.message}
        if exc.field:
            body["field"] = exc.field
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}

        location = first.get("loc", ())
        field = str(location[-1]) if location else None

        message = first.get("msg", "Datos invalidos")
        message = message.removeprefix("Value error, ")

        return JSONResponse(
            status_code=422,
            content={"detail": message, "field": field},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Error no controlado en %s %s\n%s",
            request.method,
            request.url.path,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor"},
        )

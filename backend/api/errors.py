from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi import Request


class AppError(Exception):
    """Application-level error with a machine-readable code."""

    def __init__(self, code: str, message: str, http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


ERROR_CODES = {
    "INVALID_FILE": "INVALID_FILE",
    "DOCUMENT_NOT_FOUND": "DOCUMENT_NOT_FOUND",
    "INDEXING_FAILED": "INDEXING_FAILED",
    "VECTOR_STORE_ERROR": "VECTOR_STORE_ERROR",
    "INTERNAL_SERVER_ERROR": "INTERNAL_SERVER_ERROR",
}


def _error_json(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_json(exc.code, exc.message),
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = _http_status_to_code(exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_json(code, exc.detail),
    )


def _http_status_to_code(http_status: int) -> str:
    mapping = {
        status.HTTP_400_BAD_REQUEST: "INVALID_FILE",
        status.HTTP_404_NOT_FOUND: "DOCUMENT_NOT_FOUND",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "INDEXING_FAILED",
    }
    return mapping.get(http_status, "INTERNAL_SERVER_ERROR")

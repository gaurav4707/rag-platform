from fastapi import APIRouter, UploadFile, File, HTTPException, status

from backend.config import MAX_FILE_SIZE
from backend.models.schemas import UploadResponse
from backend.services.document_service import process_upload
from backend.api.errors import AppError, ERROR_CODES

router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise AppError(
            ERROR_CODES["INVALID_FILE"],
            "Only PDF files are accepted.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    content = await file.read()

    if not content:
        raise AppError(
            ERROR_CODES["INVALID_FILE"],
            "Uploaded file is empty.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    if len(content) > MAX_FILE_SIZE:
        raise AppError(
            ERROR_CODES["FILE_TOO_LARGE"],
            "File size exceeds the maximum allowed limit.",
            http_status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    try:
        result = process_upload(content, file.filename)
    except AppError:
        raise

    return UploadResponse(**result)

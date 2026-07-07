from fastapi import APIRouter, UploadFile, File, HTTPException, status

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

    try:
        result = process_upload(content, file.filename)
    except ValueError as e:
        raise AppError(
            ERROR_CODES["INDEXING_FAILED"],
            str(e),
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return UploadResponse(**result)

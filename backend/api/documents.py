from fastapi import APIRouter

from backend.models.schemas import DocumentListItem, DeleteResponse
from backend.services.document_service import list_indexed_documents, delete_document

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentListItem])
def list_documents():
    return [DocumentListItem(**doc) for doc in list_indexed_documents()]


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document_endpoint(document_id: str):
    delete_document(document_id)
    return DeleteResponse(status="deleted")

import { useEffect, useState } from "react";
import { getDocuments, uploadDocument, deleteDocument } from "../../services/documentApi";
import type { Document } from "../../types";
import { UploadCard } from "../Upload/UploadCard";
import { DocumentList } from "../Documents/DocumentList";

export function Sidebar() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setDocumentsLoading(true);
    setDocumentsError(null);

    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error("Failed to load documents:", err);
      setDocumentsError("Failed to load documents.");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function handleUpload(file: File): Promise<void> {
    setUploading(true);
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(documentId: string, _filename: string): Promise<void> {
    setDeletingDocumentId(documentId);
    try {
      await deleteDocument(documentId);
      await loadDocuments();
    } catch (err) {
      console.error("Failed to delete document:", err);
      setDocumentsError("Failed to delete document.");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <aside className="flex w-full flex-shrink-0 flex-col overflow-hidden border-b border-gray-200 bg-white md:w-56 lg:w-72 lg:border-b-0 lg:border-r xl:w-80">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-base font-semibold text-gray-900">
          Document Q&A
        </h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-3">
        <UploadCard onUpload={handleUpload} uploading={uploading} />
        <DocumentList
          documents={documents}
          loading={documentsLoading}
          error={documentsError}
          deletingDocumentId={deletingDocumentId}
          onDelete={handleDelete}
        />
      </div>
    </aside>
  );
}

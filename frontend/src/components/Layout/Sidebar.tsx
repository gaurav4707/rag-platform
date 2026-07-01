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
    <aside className="flex w-full flex-shrink-0 flex-col overflow-hidden border-b border-surface-200 bg-white md:w-60 lg:w-72 lg:border-b-0 lg:border-r xl:w-80">
      <div className="flex items-center gap-2 border-b border-surface-200 px-4 py-3 lg:px-5">
        <svg
          className="h-4 w-4 text-surface-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776"
          />
        </svg>
        <h2 className="text-sm font-semibold tracking-tight text-surface-800">
          Documents
        </h2>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto scrollbar-thin px-4 py-4 lg:px-5">
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

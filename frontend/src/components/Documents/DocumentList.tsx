import { useState } from "react";
import type { Document } from "../../types";
import { Button } from "../ui";
import { ConfirmationDialog } from "../Common";
import { SectionTitle } from "../ui/SectionTitle";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { useSettings } from "../../context/SettingsContext";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  deletingDocumentId: string | null;
  onDelete: (documentId: string, filename: string) => void;
  onRetry: () => void;
}

export function DocumentList({
  documents,
  loading,
  error,
  deletingDocumentId,
  onDelete,
  onRetry,
}: DocumentListProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<Document | null>(null);
  const { settings } = useSettings();

  function handleDeleteClick(doc: Document) {
    if (settings.general.confirmBeforeDelete) {
      setDocToDelete(doc);
      setDialogOpen(true);
    } else {
      onDelete(doc.document_id, doc.filename);
    }
  }

  function handleConfirmDelete() {
    if (!docToDelete) return;
    setDialogOpen(false);
    onDelete(docToDelete.document_id, docToDelete.filename);
    setDocToDelete(null);
  }

  function handleCancelDelete() {
    setDialogOpen(false);
    setDocToDelete(null);
  }

  return (
    <div data-testid="document-list" aria-busy={loading}>
      <SectionTitle
        title="Library"
        count={!loading && error === null && documents.length > 0 ? documents.length : undefined}
      />

      {loading && (
        <div className="space-y-2" role="status" aria-label="Loading documents" data-testid="document-loading">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 rounded-lg border border-surface-200 px-3 py-2.5"
            >
              <div className="h-4 w-4 flex-shrink-0 rounded skeleton-shimmer animate-shimmer" />
              <div className="h-3.5 flex-1 rounded skeleton-shimmer animate-shimmer" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <ErrorState
          title="Failed to load documents"
          message="Could not retrieve your document library. Please try again."
          onRetry={onRetry}
        />
      )}

      {!loading && !error && documents.length === 0 && (
        <div className="rounded-lg border border-dashed border-surface-200 px-4 py-6" data-testid="document-empty">
          <EmptyState
            icon={
              <svg
                className="mb-2 h-6 w-6 text-surface-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v13.5c0 .621.504 1.125 1.125 1.125h10.5c.621 0 1.125-.504 1.125-1.125V11.25a9-9 0 00-9-9z"
                />
              </svg>
            }
            title={<p className="text-xs text-surface-400">No documents indexed yet</p>}
          />
        </div>
      )}

      {!loading && error === null && documents.length > 0 && (
        <ul className="space-y-1.5" data-testid="document-items">
          {documents.map((doc) => {
            const isDeleting = deletingDocumentId === doc.document_id;

            return (
              <li
                key={doc.document_id}
                className="group flex items-center gap-2.5 rounded-lg border border-surface-200 px-3 py-2.5 transition-all duration-150 hover:border-surface-300 hover:bg-surface-50 hover:shadow-subtle"
                data-testid={`document-item-${doc.document_id}`}
                data-document-id={doc.document_id}
              >
                <svg
                  className="h-4 w-4 flex-shrink-0 text-surface-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.75}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9-9 0 00-9-9z"
                  />
                </svg>

                <span
                  className="min-w-0 flex-1 truncate text-sm font-medium text-surface-700"
                  title={doc.filename}
                >
                  {doc.filename}
                </span>

                <Button
                  variant="danger"
                  onClick={() => handleDeleteClick(doc)}
                  disabled={isDeleting}
                  isLoading={isDeleting}
                  className="!h-auto !w-auto !rounded-md !p-1 bg-transparent text-surface-300 hover:bg-red-50 hover:text-red-600 group-hover:text-surface-400"
                  aria-label={`Delete ${doc.filename}`}
                >
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                    />
                  </svg>
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmationDialog
        isOpen={dialogOpen}
        title="Delete document?"
        message={docToDelete ? `Delete "${docToDelete.filename}"? This action cannot be undone.` : ""}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />
    </div>
  );
}

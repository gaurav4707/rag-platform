import type { Document } from "../../types";
import { Spinner } from "../Common/Spinner";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  deletingDocumentId: string | null;
  onDelete: (documentId: string, filename: string) => void;
}

export function DocumentList({
  documents,
  loading,
  error,
  deletingDocumentId,
  onDelete,
}: DocumentListProps) {
  function handleClick(doc: Document) {
    if (!window.confirm(`Delete '${doc.filename}'?`)) return;
    onDelete(doc.document_id, doc.filename);
  }

  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-gray-700">Documents</h3>

      {loading && (
        <div className="flex items-center gap-2 py-2" role="status" aria-label="Loading documents">
          <Spinner size="sm" />
          <span className="text-xs text-gray-400">Loading...</span>
        </div>
      )}

      {error && (
        <p className="text-xs text-red-600" role="alert">{error}</p>
      )}

      {!loading && !error && documents.length === 0 && (
        <p className="text-xs text-gray-400">No documents indexed yet.</p>
      )}

      {!loading && documents.length > 0 && (
        <ul className="space-y-1">
          {documents.map((doc) => {
            const isDeleting = deletingDocumentId === doc.document_id;

            return (
              <li
                key={doc.document_id}
                className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-gray-100"
              >
                <span
                  className="min-w-0 flex-1 truncate text-sm text-gray-700"
                  title={doc.filename}
                >
                  {doc.filename}
                </span>

                <button
                  type="button"
                  onClick={() => handleClick(doc)}
                  disabled={isDeleting}
                  className="ml-2 flex-shrink-0 rounded p-1 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={`Delete ${doc.filename}`}
                >
                  {isDeleting ? (
                    <Spinner size="sm" />
                  ) : (
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

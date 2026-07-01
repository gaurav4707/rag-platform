import { apiRequest, BASE_URL, ApiError } from "./api";
import type { UploadResponse, Document } from "../types";

/**
 * Upload a PDF file for indexing.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let code = "UPLOAD_FAILED";
    let message = "Upload failed. Please try again.";

    try {
      const body = await response.json();
      if (body?.error?.code) {
        code = body.error.code;
        message = body.error.message;
      }
    } catch {
      // Use defaults
    }

    throw new ApiError(response.status, code, message);
  }

  return response.json() as Promise<UploadResponse>;
}

/**
 * Retrieve all indexed documents.
 */
export function getDocuments(): Promise<Document[]> {
  return apiRequest<Document[]>("/documents");
}

/**
 * Delete a document by its ID.
 */
export function deleteDocument(id: string): Promise<void> {
  return apiRequest<void>(`/documents/${id}`, { method: "DELETE" });
}

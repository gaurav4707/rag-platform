import { BASE_URL, ApiError } from "./api";
import type { UploadResponse, Document } from "../types";

export interface UploadProgressCallback {
  (progress: number): void;
}

/**
 * Upload a PDF file for indexing with progress tracking.
 * Uses XMLHttpRequest for native upload progress events.
 */
export function uploadDocument(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText) as UploadResponse;
          resolve(response);
        } catch {
          reject(new ApiError(500, "INVALID_RESPONSE", "Invalid server response"));
        }
      } else {
        let code = "UPLOAD_FAILED";
        let message = "Upload failed. Please try again.";

        try {
          const body = JSON.parse(xhr.responseText);
          if (body?.error?.code) {
            code = body.error.code;
            message = body.error.message;
          }
        } catch {
          // Use defaults
        }

        reject(new ApiError(xhr.status, code, message));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new ApiError(0, "NETWORK_ERROR", "Network error. Please check your connection."));
    });

    xhr.addEventListener("abort", () => {
      reject(new DOMException("Upload cancelled", "AbortError"));
    });

    xhr.open("POST", `${BASE_URL}/documents/upload`);
    xhr.send(formData);
  });
}

/**
 * Retrieve all indexed documents.
 */
export async function getDocuments(): Promise<Document[]> {
  const response = await fetch(`${BASE_URL}/documents`, {
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new ApiError(response.status, "FETCH_FAILED", "Failed to load documents");
  }

  return response.json() as Promise<Document[]>;
}

/**
 * Delete a document by its ID.
 */
export async function deleteDocument(id: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/documents/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    let code = "DELETE_FAILED";
    let message = "Failed to delete document.";

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
}

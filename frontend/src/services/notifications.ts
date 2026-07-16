import { ToastContextType } from "../components/Common/ToastProvider";
import { mapApiError } from "./errorMapper";
import { ApiError } from "./api";

/**
 * Notification helper functions.
 * Each function accepts the toast context as a parameter.
 * This avoids global state and makes testing easier.
 */

export function notifyUploadSuccess(toast: ToastContextType, filename: string) {
  toast.success("Document Indexed", `${filename} is ready to chat.`);
}

export function notifyUploadFailed(
  toast: ToastContextType,
  error: ApiError | Error,
  onRetry?: () => void
) {
  const mapped = mapApiError(error);
  toast.error(mapped.title, mapped.description, onRetry ? { label: "Retry", onClick: onRetry } : undefined);
}

export function notifyUploadCancelled(toast: ToastContextType) {
  toast.info("Upload Cancelled", "The upload was cancelled.");
}

export function notifyDuplicateUpload(toast: ToastContextType, filename: string) {
  toast.info("Document Already Exists", `${filename} has already been uploaded.`);
}

export function notifyDeleteSuccess(toast: ToastContextType, filename: string) {
  toast.success("Document Deleted", `${filename} was removed successfully.`);
}

export function notifyDeleteFailed(
  toast: ToastContextType,
  error: ApiError | Error,
  onRetry?: () => void
) {
  const mapped = mapApiError(error);
  toast.error(mapped.title, mapped.description, onRetry ? { label: "Retry", onClick: onRetry } : undefined);
}

export function notifyChatInterrupted(
  toast: ToastContextType,
  onRetry: () => void
) {
  toast.warning("Connection Lost", "The response stream was interrupted.", { label: "Retry", onClick: onRetry });
}

export function notifyServerUnavailable(
  toast: ToastContextType,
  onRetry?: () => void
) {
  toast.error(
    "Server Unavailable",
    "The server is temporarily unavailable. Please try again in a moment.",
    onRetry ? { label: "Retry", onClick: onRetry } : undefined
  );
}

export function notifyNetworkError(
  toast: ToastContextType,
  onRetry?: () => void
) {
  toast.error(
    "Connection Error",
    "Unable to connect to the server. Please check your connection.",
    onRetry ? { label: "Retry", onClick: onRetry } : undefined
  );
}

export function notifyDocumentNotFound(toast: ToastContextType) {
  toast.error("Document Not Found", "The document may have been deleted.");
}

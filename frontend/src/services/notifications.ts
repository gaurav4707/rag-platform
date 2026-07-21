import { ToastContextType } from "../components/Common/ToastProvider";
import { mapApiError } from "./errorMapper";
import { ApiError } from "./api";

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

export function notifyChatInterrupted(toast: ToastContextType) {
  toast.warning("Connection Lost", "Response interrupted. Check your connection.");
}

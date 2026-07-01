interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

/**
 * ErrorMessage component.
 *
 * Displays an error with an optional retry button.
 */
export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4">
      <p className="text-sm text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 text-sm font-medium text-red-600 underline hover:text-red-500"
        >
          Retry
        </button>
      )}
    </div>
  );
}

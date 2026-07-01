interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div
      className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 px-3.5 py-3"
      role="alert"
    >
      <svg
        className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z"
        />
      </svg>
      <div className="flex-1">
        <p className="text-sm text-red-700">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-1.5 text-sm font-medium text-red-600 underline hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-1"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

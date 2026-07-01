import { useRef, useState, useCallback } from "react";
import { Spinner } from "../Common/Spinner";

interface UploadCardProps {
  onUpload: (file: File) => Promise<void>;
  uploading: boolean;
}

const ACCEPTED_TYPE = "application/pdf";

export function UploadCard({ onUpload, uploading }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  const validateAndUpload = useCallback(
    async (file: File) => {
      setError(null);

      if (!file) return;

      if (file.type !== ACCEPTED_TYPE) {
        setError("Only PDF files are accepted.");
        return;
      }

      if (file.size === 0) {
        setError("Uploaded file is empty.");
        return;
      }

      if (uploading) return;

      try {
        await onUpload(file);
      } catch (err) {
        console.error("Upload failed:", err);
        setError("Upload failed. Please try again.");
      }
    },
    [onUpload, uploading],
  );

  function handleClick() {
    if (uploading) return;
    setError(null);
    inputRef.current?.click();
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    validateAndUpload(file);
    e.target.value = "";
  }

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      dragCounter.current = 0;

      const file = e.dataTransfer.files?.[0];
      if (!file) return;
      validateAndUpload(file);
    },
    [validateAndUpload],
  );

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
        aria-hidden="true"
      />

      {uploading ? (
        <div className="flex items-center justify-center gap-2.5 rounded-xl border-2 border-dashed border-surface-200 bg-surface-50 px-4 py-5">
          <Spinner size="sm" />
          <span className="text-sm text-surface-500">Uploading...</span>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={0}
          onClick={handleClick}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleClick();
            }
          }}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={`group w-full cursor-pointer rounded-xl border-2 border-dashed px-4 py-5 text-center transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2 ${
            isDragging
              ? "border-accent-400 bg-accent-50 shadow-drop scale-[1.01]"
              : "border-surface-300 bg-surface-50 hover:border-accent-300 hover:bg-accent-50/40"
          }`}
          aria-label="Upload a PDF document"
        >
          {isDragging ? (
            <div className="flex flex-col items-center gap-1.5 animate-fade-in">
              <svg
                className="h-7 w-7 text-accent-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
              <p className="text-sm font-medium text-accent-700">Drop your PDF here</p>
              <p className="text-xs text-accent-500">Release to upload</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1.5">
              <svg
                className="h-7 w-7 text-surface-400 transition-colors group-hover:text-accent-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.75}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"
                />
              </svg>
              <p className="text-sm font-medium text-surface-600">Upload a PDF document</p>
              <p className="text-xs text-surface-400">Click or drag and drop</p>
            </div>
          )}
        </div>
      )}

      {error && (
        <div
          className="mt-2 flex items-center gap-1.5 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 animate-slide-up"
          role="alert"
        >
          <svg
            className="h-3.5 w-3.5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}

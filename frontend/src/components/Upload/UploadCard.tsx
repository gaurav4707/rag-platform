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

  const dropZoneClass = uploading
    ? "border-gray-200 bg-gray-50"
    : isDragging
      ? "border-blue-400 bg-blue-50"
      : "border-gray-300 hover:border-gray-400";

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
        <div className="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-4">
          <Spinner size="sm" />
          <span className="text-sm text-gray-500">Uploading...</span>
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
          className={`w-full cursor-pointer rounded-lg border-2 border-dashed p-4 text-center transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${dropZoneClass}`}
          aria-label="Upload a PDF document"
        >
          {isDragging ? (
            <>
              <p className="text-sm text-blue-600">Drop your PDF here</p>
              <p className="mt-1 text-xs text-blue-400">Release to upload</p>
            </>
          ) : (
            <>
              <p className="text-sm text-gray-500">Upload a PDF document</p>
              <p className="mt-1 text-xs text-gray-400">Click or drag and drop</p>
            </>
          )}
        </div>
      )}

      {error && (
        <p className="mt-2 text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

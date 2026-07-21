import { useRef, useState, useCallback, useEffect } from "react";
import { Spinner } from "../Common/Spinner";
import { useToast } from "../../hooks/useToast";
import { notifyUploadFailed, notifyUploadCancelled } from "../../services/notifications";
import type { UploadProgressCallback } from "../../services/documentApi";

export type UploadStatus = "idle" | "uploading" | "processing" | "error";

interface UploadCardProps {
  onUpload: (file: File, onProgress?: UploadProgressCallback) => Promise<void>;
}

const ACCEPTED_TYPE = "application/pdf";

export function UploadCard({ onUpload }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [displayProgress, setDisplayProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [hasRealProgress, setHasRealProgress] = useState(false);
  const dragCounter = useRef(0);
  const abortControllerRef = useRef<XMLHttpRequest | null>(null);
  const autoResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressAnimationRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const toast = useToast();

  useEffect(() => {
    return () => {
      resetUploadState();
    };
  }, []);

  const clearAutoResetTimer = useCallback(() => {
    if (autoResetTimerRef.current) {
      clearTimeout(autoResetTimerRef.current);
      autoResetTimerRef.current = null;
    }
  }, []);

  const handleAutoReset = useCallback((delay: number) => {
    clearAutoResetTimer();
    autoResetTimerRef.current = setTimeout(() => {
      setStatus("idle");
      setDisplayProgress(0);
      setError(null);
      setHasRealProgress(false);
      abortControllerRef.current = null;
    }, delay);
  }, [clearAutoResetTimer]);

  const animateProgress = useCallback((target: number) => {
    const start = displayProgress;
    const duration = 300;
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;
      setDisplayProgress(Math.round(current));

      if (progress < 1) {
        progressAnimationRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayProgress(target);
      }
    };

    if (progressAnimationRef.current) {
      cancelAnimationFrame(progressAnimationRef.current);
    }
    progressAnimationRef.current = requestAnimationFrame(animate);
  }, [displayProgress]);

  const handleProgress = useCallback((p: number) => {
    if (p > 0 && p < 100) {
      setHasRealProgress(true);
    }
    animateProgress(p);
  }, [animateProgress]);

  const resetUploadState = useCallback(() => {
    clearAutoResetTimer();
    if (progressAnimationRef.current) {
      cancelAnimationFrame(progressAnimationRef.current);
      progressAnimationRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("idle");
    setDisplayProgress(0);
    setError(null);
    setHasRealProgress(false);
    setIsDragging(false);
    dragCounter.current = 0;
  }, [clearAutoResetTimer]);

  const validateAndUpload = useCallback(
    async (file: File) => {
      if (status !== "idle") return;

      resetUploadState();
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

      try {
        setStatus("uploading");
        setDisplayProgress(0);
        setHasRealProgress(false);

        await onUpload(file, handleProgress);

        setStatus("processing");

        // Success - reset to idle, Sidebar toast will show success
        setStatus("idle");
        setDisplayProgress(0);
        setHasRealProgress(false);

      } catch (err) {
        console.error("Upload failed:", err);

        if (err instanceof DOMException && err.name === "AbortError") {
          notifyUploadCancelled(toast);
          resetUploadState();
          return;
        }

        setStatus("error");
        notifyUploadFailed(toast, err instanceof Error ? err : new Error(String(err)));
        handleAutoReset(2000);
      }
    },
    [onUpload, handleProgress, handleAutoReset, resetUploadState, toast, status],
  );

  function handleClick() {
    if (status !== "idle") return;
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


  const getMainContent = () => {
    if (isDragging) {
      return (
        <div className="flex flex-col items-center gap-1.5 animate-fade-in">
          <svg className="h-7 w-7 text-accent-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          <p className="text-sm font-medium text-accent-700 dark:text-accent-300">Drop your PDF here</p>
          <p className="text-xs text-accent-500 dark:text-accent-400">Release to upload</p>
        </div>
      );
    }

    switch (status) {
      case "uploading":
        return (
          <div className="flex items-center gap-2.5">
            <Spinner size="sm" />
            <span className="text-sm text-surface-500 dark:text-surface-400">
              {hasRealProgress ? `Uploading... ${displayProgress}%` : "Uploading..."}
            </span>
          </div>
        );
      case "processing":
        return (
          <div className="flex items-center gap-2.5">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" aria-hidden="true" />
            <span className="text-sm text-surface-500 dark:text-surface-400">Processing document...</span>
          </div>
        );
      case "error":
        return (
          <div className="flex flex-col items-center gap-1.5 text-red-600 dark:text-red-400">
            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium">Upload failed</p>
            <p className="text-xs text-red-500 dark:text-red-400">Click to try again</p>
          </div>
        );
      default:
        return (
          <div className="flex flex-col items-center gap-1.5">
            <svg className="h-7 w-7 text-surface-400 transition-colors group-hover:text-accent-400 dark:text-surface-400 dark:group-hover:text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
            <p className="text-sm font-medium text-surface-600 dark:text-surface-400">Upload a PDF document</p>
            <p className="text-xs text-surface-400 dark:text-surface-400">Click or drag and drop</p>
          </div>
        );
    }
  };

  // Card always uses idle styling - no visual disabled state
  const cardClassName = `group w-full cursor-pointer rounded-xl border-2 border-dashed px-4 py-5 text-center transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:ring-offset-2 ${
    isDragging
      ? "border-accent-400 bg-accent-50 shadow-drop scale-[1.01] dark:border-accent-400 dark:bg-accent-900/20"
      : "border-surface-300 bg-surface-50 hover:border-accent-300 hover:bg-accent-50/40 dark:border-surface-600 dark:hover:border-accent-700 dark:hover:bg-accent-900/20"
  }`;

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
        aria-hidden="true"
        disabled={status !== "idle"}
        data-testid="file-input"
      />

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
        className={cardClassName}
        aria-label="Upload a PDF document"
        data-testid="upload-dropzone"
      >
        {getMainContent()}
      </div>

      {(status === "uploading" || status === "processing") && (
        <div className="mt-2 w-full" role="progressbar" aria-valuenow={status === "uploading" && hasRealProgress ? displayProgress : undefined} aria-valuemin={0} aria-valuemax={100} aria-label={status === "uploading" ? "Upload progress" : "Processing progress"} data-testid="upload-progress">
          <div className="h-1.5 w-full rounded-full bg-surface-200 dark:bg-surface-700 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ease-out ${
                status === "processing" || !hasRealProgress
                  ? "bg-accent-500 animate-pulse-soft"
                  : "bg-accent-600 dark:bg-accent-500"
              }`}
              style={{ width: status === "uploading" && hasRealProgress ? `${displayProgress}%` : "100%" }}
              aria-hidden="true"
            />
          </div>
        </div>
      )}

      {error && (
        <div
          className="mt-2 flex items-center gap-1.5 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 animate-slide-up dark:bg-red-900/20 dark:text-red-300"
          role="alert"
          data-testid="upload-error"
        >
          <svg className="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}

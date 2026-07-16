import { useEffect, useRef, useState } from "react";

export type ToastVariant = "success" | "info" | "warning" | "error";

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface Toast {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  action?: ToastAction;
  duration?: number;
}

interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const variantStyles: Record<ToastVariant, string> = {
  success: "border-emerald-200 bg-white text-surface-800 dark:bg-surface-900 dark:border-emerald-800 dark:text-surface-50",
  info: "border-blue-200 bg-white text-surface-800 dark:bg-surface-900 dark:border-blue-800 dark:text-surface-50",
  warning: "border-amber-200 bg-white text-surface-800 dark:bg-surface-900 dark:border-amber-800 dark:text-surface-50",
  error: "border-red-200 bg-white text-surface-800 dark:bg-surface-900 dark:border-red-800 dark:text-surface-50",
};

const variantIcons: Record<ToastVariant, React.ReactNode> = {
  success: (
    <svg className="h-4.5 w-4.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
    </svg>
  ),
  info: (
    <svg className="h-4.5 w-4.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  ),
  warning: (
    <svg className="h-4.5 w-4.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
    </svg>
  ),
  error: (
    <svg className="h-4.5 w-4.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

const variantIconColors: Record<ToastVariant, string> = {
  success: "text-emerald-500",
  info: "text-blue-500",
  warning: "text-amber-500",
  error: "text-red-500",
};

const variantBgAccents: Record<ToastVariant, string> = {
  success: "bg-emerald-500",
  info: "bg-blue-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
};

export function ToastComponent({ toast, onClose }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleActionClick = () => {
    if (toast.action) {
      toast.action.onClick();
      onClose(toast.id);
    }
  };

  const handleCloseClick = () => {
    startExit();
  };

  const startExit = () => {
    setIsExiting(true);
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setTimeout(() => onClose(toast.id), 200);
  };

  useEffect(() => {
    containerRef.current?.focus();

    if (toast.duration && toast.duration > 0) {
      const steps = 60;
      const interval = toast.duration / steps;
      let current = 0;

      progressIntervalRef.current = setInterval(() => {
        current += 1;
        setProgress((current / steps) * 100);
        if (current >= steps) {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
          }
          startExit();
        }
      }, interval);
    }

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [toast.duration, toast.id]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleCloseClick();
    }
    if (e.key === "Enter" && toast.action) {
      handleActionClick();
    }
  };

  const bgAccent = variantBgAccents[toast.variant];
  const iconColor = variantIconColors[toast.variant];
  const style = variantStyles[toast.variant];
  const icon = variantIcons[toast.variant];

  return (
    <div
      ref={containerRef}
      className={`relative flex items-start gap-3 rounded-xl border p-3.5 shadow-lg animate-slide-in-right ${style} ${isExiting ? "animate-slide-out-right" : ""}`}
      role="alert"
      aria-live="polite"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      style={{ minWidth: "360px", maxWidth: "420px" }}
    >
      <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-xl">
        <div className={`${bgAccent} h-full rounded-l-xl`} />
      </div>
      <div className={`flex-shrink-0 mt-0.5 ${iconColor}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium leading-tight">{toast.title}</p>
        {toast.description && (
          <p className="mt-1 text-sm opacity-75 leading-relaxed">{toast.description}</p>
        )}
        {toast.action && (
          <button
            onClick={handleActionClick}
            className="mt-2.5 text-sm font-medium underline hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-surface-900"
            type="button"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={handleCloseClick}
        className="flex-shrink-0 rounded p-1 opacity-40 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-surface-900"
        aria-label="Dismiss"
        type="button"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      {toast.duration && toast.duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1" style={{ backgroundColor: "rgba(0,0,0,0.08)" }}>
          <div
            className={`${bgAccent} h-full transform-origin-left`}
            style={{
              transform: `scaleX(${1 - progress / 100})`,
              transformOrigin: "left center",
            }}
          />
        </div>
      )}
    </div>
  );
}

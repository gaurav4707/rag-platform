import { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from "react";
import { Toast, ToastVariant, ToastAction } from "./Toast";

export interface ToastContextType {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, "id">) => string;
  dismissToast: (id: string) => void;
  success: (title: string, description?: string, action?: ToastAction) => string;
  info: (title: string, description?: string, action?: ToastAction) => string;
  warning: (title: string, description?: string, action?: ToastAction) => string;
  error: (title: string, description?: string, action?: ToastAction) => string;
}

const ToastContext = createContext<ToastContextType | null>(null);

const DEFAULT_DURATIONS: Record<ToastVariant, number> = {
  success: 4000,
  info: 4000,
  warning: 7000,
  error: 7000,
};

const MAX_VISIBLE_TOASTS = 3;

function toastKey(toast: Omit<Toast, "id">): string {
  return `${toast.variant}:${toast.title}:${toast.description ?? ""}`;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timeoutIdRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const generateId = useCallback(() => Math.random().toString(36).slice(2, 9), []);

  const showToast = useCallback(
    (toast: Omit<Toast, "id">) => {
      const key = toastKey(toast);
      const existingIndex = toasts.findIndex((t) => toastKey(t) === key);
      if (existingIndex !== -1) {
        return toasts[existingIndex].id;
      }

      const id = generateId();
      const duration = toast.duration ?? DEFAULT_DURATIONS[toast.variant];
      const newToast: Toast = { ...toast, id, duration };

      setToasts((prev) => {
        const next = [...prev, newToast];
        if (next.length > MAX_VISIBLE_TOASTS) {
          const toRemove = next.length - MAX_VISIBLE_TOASTS;
          next.splice(0, toRemove);
        }
        return next;
      });

      if (duration > 0 && !toast.action) {
        const timeoutId = setTimeout(() => {
          if (mountedRef.current) {
            setToasts((prev) => prev.filter((t) => t.id !== id));
            timeoutIdRef.current.delete(id);
          }
        }, duration);
        timeoutIdRef.current.set(id, timeoutId);
      }

      return id;
    },
    [toasts, generateId]
  );

  const dismissToast = useCallback((id: string) => {
    const timeoutId = timeoutIdRef.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutIdRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => {
    return () => {
      timeoutIdRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
      timeoutIdRef.current.clear();
    };
  }, []);

  const success = useCallback(
    (title: string, description?: string, action?: ToastAction) =>
      showToast({ variant: "success", title, description, action }),
    [showToast]
  );

  const info = useCallback(
    (title: string, description?: string, action?: ToastAction) =>
      showToast({ variant: "info", title, description, action }),
    [showToast]
  );

  const warning = useCallback(
    (title: string, description?: string, action?: ToastAction) =>
      showToast({ variant: "warning", title, description, action }),
    [showToast]
  );

  const error = useCallback(
    (title: string, description?: string, action?: ToastAction) =>
      showToast({ variant: "error", title, description, action }),
    [showToast]
  );

  return (
    <ToastContext.Provider
      value={{
        toasts,
        showToast,
        dismissToast,
        success,
        info,
        warning,
        error,
      }}
    >
      {children}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

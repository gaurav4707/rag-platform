import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useToast } from "./ToastProvider";
import { ToastComponent } from "./Toast";

export function ToastContainer() {
  const { toasts, dismissToast } = useToast();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const container = document.createElement("div");
    container.className = "fixed top-20 right-6 z-[100] flex flex-col-reverse gap-2 pointer-events-none w-[400px] max-w-[90vw]";
    container.setAttribute("aria-live", "polite");
    container.setAttribute("aria-label", "Notifications");
    container.setAttribute("data-testid", "toast-container");
    document.body.appendChild(container);
    containerRef.current = container;
    setMounted(true);

    return () => {
      if (containerRef.current) {
        document.body.removeChild(containerRef.current);
        containerRef.current = null;
      }
    };
  }, []);

  if (!mounted || toasts.length === 0) {
    return null;
  }

  const content = (
    <div data-testid="toast-container" className="pointer-events-none">
      {toasts.slice().reverse().map((toast) => (
        <div key={toast.id} className="pointer-events-auto w-full" data-testid={`toast-${toast.variant}`}>
          <ToastComponent toast={toast} onClose={dismissToast} />
        </div>
      ))}
    </div>
  );

  return createPortal(content, containerRef.current!);
}

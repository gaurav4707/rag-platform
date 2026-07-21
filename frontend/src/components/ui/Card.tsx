import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: boolean;
  hover?: boolean;
}

export function Card({ children, className = "", padding = true, hover = false }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-surface-200 ${
        padding ? "px-3 py-2.5" : ""
      } ${hover ? "transition-colors hover:bg-surface-50" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

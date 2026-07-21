import type { ReactNode } from "react";
import { Button } from "../Common/Button";

interface EmptyStateProps {
  icon?: ReactNode;
  title: ReactNode;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ icon, title, description, action, className = "" }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center text-center animate-fade-in ${className}`}>
      {icon}
      {typeof title === "string" ? (
        <h2 className="mb-1.5 text-lg font-semibold text-surface-800">{title}</h2>
      ) : (
        title
      )}
      {description && (
        <p className="text-sm leading-relaxed text-surface-500">{description}</p>
      )}
      {action && (
        <div className="mt-4">
          <Button variant="primary" onClick={action.onClick}>
            {action.label}
          </Button>
        </div>
      )}
    </div>
  );
}

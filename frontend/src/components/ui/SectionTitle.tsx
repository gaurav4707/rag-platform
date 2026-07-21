import type { ReactNode } from "react";

interface SectionTitleProps {
  title: string;
  count?: number;
  action?: ReactNode;
  className?: string;
}

export function SectionTitle({ title, count, action, className = "" }: SectionTitleProps) {
  return (
    <div className={`mb-2.5 flex items-center justify-between ${className}`}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-surface-500">
        {title}
      </h3>
      {count != null && (
        <span className="text-xs font-medium text-surface-400">
          {count} {count === 1 ? "file" : "files"}
        </span>
      )}
      {action}
    </div>
  );
}

import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "success" | "warning" | "error";
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: "bg-surface-100 text-surface-600",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  error: "bg-red-50 text-red-700",
};

const dotStyles: Record<string, string> = {
  default: "bg-surface-400",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
};

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${variantStyles[variant]} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotStyles[variant]}`} />
      {children}
    </span>
  );
}

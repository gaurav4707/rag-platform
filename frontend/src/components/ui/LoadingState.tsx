import { Spinner } from "../Common/Spinner";

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingState({ label, className = "" }: LoadingStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 px-6 py-12 ${className}`} role="status" aria-label={label ?? "Loading"}>
      <Spinner size="lg" />
      {label && (
        <p className="text-sm text-surface-500">{label}</p>
      )}
    </div>
  );
}

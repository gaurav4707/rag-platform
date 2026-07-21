import { Badge } from "../ui/Badge";

export function Header() {
  return (
    <header className="flex flex-shrink-0 items-center gap-3 border-b border-surface-200 bg-white px-4 py-3 lg:px-6 lg:py-3.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-600 shadow-subtle">
        <svg
          className="h-4.5 w-4.5 text-white"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.236 1.169.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
          />
        </svg>
      </div>

      <div className="flex items-baseline gap-2">
        <h1 className="text-base font-semibold tracking-tight text-surface-900 lg:text-lg">
          RAG Agent
        </h1>
        <span className="hidden text-xs font-medium text-surface-400 sm:inline">
          Document Q&A
        </span>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Badge variant="success">Online</Badge>
      </div>
    </header>
  );
}

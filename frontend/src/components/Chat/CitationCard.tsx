interface CitationCardProps {
  document: string;
  page: number | null;
}

export function CitationCard({ document: filename, page }: CitationCardProps) {
  return (
    <div className="flex items-center gap-2.5 rounded-lg border border-surface-200 bg-surface-50 px-3 py-2 transition-colors hover:border-surface-300 hover:bg-surface-100/60">
      <svg
        className="h-4 w-4 flex-shrink-0 text-surface-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.75}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9-9 0 00-9-9z"
        />
      </svg>

      <div className="min-w-0 flex-1">
        <p
          className="truncate text-xs font-medium text-surface-700"
          title={filename}
        >
          {filename}
        </p>
        {page != null && (
          <p className="mt-0.5 text-xs text-surface-400">Page {page}</p>
        )}
      </div>
    </div>
  );
}

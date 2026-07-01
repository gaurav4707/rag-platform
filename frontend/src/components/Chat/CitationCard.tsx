interface CitationCardProps {
  document: string;
  page: number | null;
  score: number | null;
}

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function CitationCard({ document: filename, page, score }: CitationCardProps) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <svg
        className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>

      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium text-gray-700" title={filename}>
          {filename}
        </p>
        <div className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-gray-400">
          {page != null && <span>p.{page}</span>}
          {score != null && <span>{formatScore(score)}</span>}
        </div>
      </div>
    </div>
  );
}

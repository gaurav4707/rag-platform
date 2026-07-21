import { useState, memo } from "react";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui";
import { useToast } from "../Common";
import type { CitationViewModel } from "../../utils/citationUtils";
import { formatPageRef, formatScore, copyCitation, copyDocument, copyPage } from "../../utils/citationUtils";

interface CitationCardProps {
  citation: CitationViewModel;
}

function notifyCopy(toast: ReturnType<typeof useToast>, label: string) {
  toast.success("Copied", `${label} copied to clipboard.`);
}

export const CitationCard = memo(function CitationCard({ citation }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const toast = useToast();

  async function handleCopyCitation() {
    await copyCitation(citation);
    notifyCopy(toast, "Citation text");
  }

  async function handleCopyDocument() {
    await copyDocument(citation);
    notifyCopy(toast, "Document name");
  }

  async function handleCopyPage() {
    if (citation.page == null) return;
    await copyPage(citation);
    notifyCopy(toast, "Page reference");
  }

  const pageRef = formatPageRef(citation.page);
  const scoreText = formatScore(citation.score);

  return (
    <Card padding={false} className="transition-colors hover:border-surface-300">
      <div className="px-3 py-2">
        <div className="flex items-center gap-2.5">
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

          <span
            className="min-w-0 flex-1 truncate text-sm font-medium text-surface-700"
            title={citation.filename}
          >
            {citation.filename}
          </span>

          <div className="flex items-center gap-1.5">
            {pageRef && <Badge variant="default">{pageRef}</Badge>}
            {scoreText && <Badge variant="default">{scoreText}</Badge>}
          </div>

          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-600 focus:outline-none focus:ring-2 focus:ring-surface-400"
            aria-expanded={expanded}
            aria-label={expanded ? "Hide citation details" : "Show citation details"}
          >
            <svg
              className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>
        </div>

        {expanded && (
          <div className="mt-3 space-y-2.5 border-t border-surface-100 pt-2.5 animate-slide-up">
            {pageRef && (
              <p className="text-xs text-surface-500">
                Page <span className="font-medium text-surface-700">{citation.page}</span>
              </p>
            )}
            {scoreText && (
              <p className="text-xs text-surface-500">
                Relevance <span className="font-medium text-surface-700">{scoreText}</span>
              </p>
            )}

            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                onClick={handleCopyCitation}
                className="!h-auto !px-2.5 !py-1.5 !text-xs"
              >
                Copy Citation
              </Button>
              <Button
                variant="secondary"
                onClick={handleCopyDocument}
                className="!h-auto !px-2.5 !py-1.5 !text-xs"
              >
                Copy Document
              </Button>
              {pageRef && (
                <Button
                  variant="secondary"
                  onClick={handleCopyPage}
                  className="!h-auto !px-2.5 !py-1.5 !text-xs"
                >
                  Copy Page
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
});

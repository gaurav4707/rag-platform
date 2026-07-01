import type { Source } from "../../types";
import { CitationCard } from "./CitationCard";

interface MessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export function Message({ role, content, sources, isStreaming }: MessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex animate-slide-up ${isUser ? "justify-end" : "justify-start"}`}
    >
      {isUser ? (
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent-600 px-4 py-2.5 text-white shadow-card lg:max-w-[75%]">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      ) : (
        <div className="flex max-w-[85%] gap-3 lg:max-w-[80%]">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-surface-100 shadow-subtle">
            <svg
              className="h-4 w-4 text-surface-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"
              />
            </svg>
          </div>

          <div className="min-w-0 flex-1">
            <div className="rounded-2xl rounded-tl-md border border-surface-200 bg-white px-4 py-2.5 shadow-card">
              <p className="text-sm leading-relaxed whitespace-pre-wrap text-surface-800">
                {content}
                {isStreaming && (
                  <span
                    className="ml-0.5 inline-block h-[1em] w-[2px] translate-y-[2px] bg-accent-500 animate-blink"
                    aria-label="Generating response"
                  />
                )}
              </p>
            </div>

            {sources && sources.length > 0 && !isStreaming && (
              <div className="mt-2.5 space-y-1.5">
                <p className="px-1 text-xs font-medium uppercase tracking-wider text-surface-400">
                  Sources
                </p>
                {sources.map((source, idx) => (
                  <CitationCard
                    key={`${source.document_id}-${idx}`}
                    document={source.document}
                    page={source.page}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

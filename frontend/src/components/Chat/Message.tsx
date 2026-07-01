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
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[90%] break-words rounded-lg px-3 py-2 lg:max-w-[80%] lg:px-4 ${
          isUser
            ? "bg-blue-600 text-white"
            : "border border-gray-200 bg-white text-gray-900"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">
          {content}
          {isStreaming && (
            <span
              className="inline-block w-[2px] h-[1em] bg-gray-400 ml-0.5 animate-pulse"
              aria-label="Generating response"
            />
          )}
        </p>

        {sources && sources.length > 0 && !isStreaming && (
          <div className="mt-3 space-y-2">
            {sources.map((source, idx) => (
              <CitationCard
                key={`${source.document_id}-${idx}`}
                document={source.document}
                page={source.page}
                score={source.score}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

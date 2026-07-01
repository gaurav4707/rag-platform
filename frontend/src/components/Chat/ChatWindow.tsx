import { useEffect, useRef } from "react";
import { Message } from "./Message";
import type { Message as MessageType } from "../../types";

interface ChatWindowProps {
  messages: MessageType[];
}

export function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin">
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center px-6">
          <div className="flex max-w-md flex-col items-center text-center animate-fade-in">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-50 shadow-subtle">
              <svg
                className="h-7 w-7 text-accent-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.75}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z"
                />
              </svg>
            </div>
            <h2 className="mb-1.5 text-lg font-semibold text-surface-800">
              Ask a question about your documents
            </h2>
            <p className="text-sm leading-relaxed text-surface-500">
              Upload a PDF to get started, then ask anything. Answers are
              grounded in your indexed documents with inline citations.
            </p>
          </div>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-3xl space-y-5 px-4 py-6 lg:px-6 lg:py-8">
          {messages.map((msg) => (
            <Message
              key={msg.id}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
              isStreaming={msg.isStreaming}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}

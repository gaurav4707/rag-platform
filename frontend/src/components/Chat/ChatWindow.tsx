import { useEffect, useRef } from "react";
import { Message } from "./Message";
import { EmptyState } from "../ui/EmptyState";
import type { Message as MessageType } from "../../types";

interface ChatWindowProps {
  messages: MessageType[];
  onRetry?: () => void;
}

export function ChatWindow({ messages, onRetry }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const streaming = messages.some(m => m.state === "streaming" || m.state === "pending");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin" aria-busy={streaming} role="region" aria-label="Chat messages">
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center px-6">
          <div className="max-w-md">
            <EmptyState
              icon={
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
              }
              title="Ask a question about your documents"
              description="Upload a PDF to get started, then ask anything. Answers are grounded in your indexed documents with inline citations."
            />
          </div>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-3xl space-y-5 px-4 py-6 lg:px-6 lg:py-8" aria-live="polite" aria-atomic="false">
          {messages.map((msg) => (
            <Message
              key={msg.id}
              role={msg.role}
              content={msg.content}
              state={msg.state}
              sources={msg.sources}
              onRetry={msg.state === "interrupted" ? onRetry : undefined}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}

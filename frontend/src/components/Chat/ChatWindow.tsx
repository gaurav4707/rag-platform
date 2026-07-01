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
    <div className="flex-1 overflow-y-auto px-3 py-3 lg:px-6 lg:py-4">
      {messages.length === 0 && (
        <div className="flex h-full items-center justify-center">
          <p className="text-sm text-gray-400">
            Ask a question about your documents.
          </p>
        </div>
      )}

      <div className="space-y-3 lg:space-y-4">
        {messages.map((msg) => (
          <Message
            key={msg.id}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
            isStreaming={msg.isStreaming}
          />
        ))}
      </div>

      <div ref={bottomRef} />
    </div>
  );
}

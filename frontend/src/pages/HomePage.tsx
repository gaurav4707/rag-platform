import { useState, useRef, useCallback } from "react";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { ChatInput } from "../components/Chat/ChatInput";
import { streamMessage } from "../services/chatApi";
import type { Message as MessageType, Source } from "../types";

let nextId = 1;

export function HomePage() {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [streaming, setStreaming] = useState(false);
  const assistantIdRef = useRef<string | null>(null);

  const appendToLastMessage = useCallback((updater: (last: MessageType) => MessageType) => {
    setMessages((prev) => {
      const updated = prev.slice();
      const last = updated[updated.length - 1];
      if (last && last.id === assistantIdRef.current) {
        updated[updated.length - 1] = updater(last);
      }
      return updated;
    });
  }, []);

  const handleSend = useCallback(
    (text: string) => {
      if (streaming) return;

      const assistantId = String(nextId++);
      assistantIdRef.current = assistantId;

      const userMsg: MessageType = {
        id: String(nextId++),
        role: "user",
        content: text,
      };

      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: assistantId, role: "assistant", content: "", isStreaming: true },
      ]);

      setStreaming(true);

      streamMessage(text, {
        onToken: (token) => {
          appendToLastMessage((last) => ({
            ...last,
            content: last.content + token,
          }));
        },
        onDone: (sources: Source[]) => {
          appendToLastMessage((last) => ({
            ...last,
            sources,
            isStreaming: false,
          }));
          setStreaming(false);
          assistantIdRef.current = null;
        },
        onError: (err) => {
          console.error("Stream error:", err);
          appendToLastMessage((last) => ({
            ...last,
            content: "Sorry, something went wrong.",
            isStreaming: false,
          }));
          setStreaming(false);
          assistantIdRef.current = null;
        },
      });
    },
    [streaming, appendToLastMessage],
  );

  return (
    <>
      <ChatWindow messages={messages} />
      <ChatInput onSend={handleSend} disabled={streaming} />
    </>
  );
}

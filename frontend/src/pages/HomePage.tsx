import { useState, useRef, useCallback } from "react";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { ChatInput } from "../components/Chat/ChatInput";
import { streamMessage } from "../services/chatApi";
import { useToast } from "../components/Common";
import {
  notifyChatInterrupted,
} from "../services/notifications";
import type { Message as MessageType, Source } from "../types";

let nextId = 1;

export function HomePage() {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [streaming, setStreaming] = useState(false);
  const assistantIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastUserMessageRef = useRef<string | null>(null);
  const toast = useToast();

  const appendToLastMessage = useCallback((assistantId: string | null, updater: (last: MessageType) => MessageType) => {
    if (!assistantId) return;
    setMessages((prev) => {
      const updated = prev.slice();
      const last = updated[updated.length - 1];
      if (last && last.id === assistantId) {
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
      lastUserMessageRef.current = text;

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
      abortControllerRef.current = new AbortController();

      streamMessage(text, {
        onToken: (token) => {
          appendToLastMessage(assistantId, (last) => ({
            ...last,
            content: last.content + token,
          }));
        },
        onDone: (sources: Source[]) => {
          const assistantId = assistantIdRef.current;
          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === assistantId) {
              updated[updated.length - 1] = { ...last, sources, isStreaming: false };
            }
            return updated;
          });
          setStreaming(false);
          assistantIdRef.current = null;
          abortControllerRef.current = null;
        },
        onError: (err) => {
          console.error("Stream error:", err);
          const assistantId = assistantIdRef.current;
          
          if (err instanceof DOMException && err.name === "AbortError") {
            return;
          }

          // Preserve partial response, add inline warning
          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === assistantId) {
              updated[updated.length - 1] = { 
                ...last, 
                isStreaming: false,
                streamInterrupted: true,
              };
            }
            return updated;
          });
          
          setStreaming(false);
          assistantIdRef.current = null;
          abortControllerRef.current = null;
          
          // Show toast notification for stream interruption
          notifyChatInterrupted(toast, () => {
            if (lastUserMessageRef.current) {
              handleSend(lastUserMessageRef.current);
            }
          });
        },
      }, abortControllerRef.current.signal);
    },
    [streaming, appendToLastMessage, toast],
  );

  const handleRetry = useCallback(() => {
    if (lastUserMessageRef.current) {
      handleSend(lastUserMessageRef.current);
    }
  }, [handleSend]);

  return (
    <>
      <ChatWindow messages={messages} onRetry={handleRetry} />
      <ChatInput onSend={handleSend} disabled={streaming} />
    </>
  );
}

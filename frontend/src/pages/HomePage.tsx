import { useState, useRef, useCallback } from "react";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { ChatInput } from "../components/Chat/ChatInput";
import { streamMessage } from "../services/chatApi";
import { useToast } from "../components/Common";
import {
  notifyChatInterrupted,
} from "../services/notifications";
import type { Message as MessageType, Source, MessageState } from "../types";

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
        { id: assistantId, role: "assistant", content: "", state: "pending" as MessageState },
      ]);

      setStreaming(true);
      abortControllerRef.current = new AbortController();

      streamMessage(text, {
        onToken: (token) => {
          appendToLastMessage(assistantId, (last) => ({
            ...last,
            state: "streaming" as MessageState,
            content: last.content + token,
          }));
        },
        onDone: (sources: Source[]) => {
          const assistantId = assistantIdRef.current;
          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === assistantId) {
              updated[updated.length - 1] = { ...last, sources, state: "complete" as MessageState };
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

          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === assistantId) {
              updated[updated.length - 1] = { 
                ...last, 
                state: "interrupted" as MessageState,
              };
            }
            return updated;
          });
          
          setStreaming(false);
          assistantIdRef.current = null;
          abortControllerRef.current = null;
          
          notifyChatInterrupted(toast);
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

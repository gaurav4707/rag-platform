import { createContext, useContext, useState, useCallback, useRef } from "react";
import type { ReactNode } from "react";
import type { Message, Source, MessageState } from "../types";
import { streamMessage } from "../services/chatApi";
import { useToast } from "../components/Common";
import { notifyChatInterrupted } from "../services/notifications";

interface ConversationContextValue {
  messages: Message[];
  streaming: boolean;
  conversationVersion: number;
  send: (text: string) => void;
  retry: () => void;
  resetConversation: () => void;
}

const ConversationContext = createContext<ConversationContextValue | null>(null);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [conversationVersion, setConversationVersion] = useState(0);

  const nextIdRef = useRef(1);
  const assistantIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastUserMessageRef = useRef<string | null>(null);
  const toast = useToast();

  const appendToLastMessage = useCallback((assistantId: string | null, updater: (last: Message) => Message) => {
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

  const send = useCallback(
    (text: string) => {
      if (streaming) return;

      const assistantId = String(nextIdRef.current++);
      assistantIdRef.current = assistantId;
      lastUserMessageRef.current = text;

      const userMsg: Message = {
        id: String(nextIdRef.current++),
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
          const currentAssistantId = assistantIdRef.current;
          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === currentAssistantId) {
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

          if (err instanceof DOMException && err.name === "AbortError") {
            return;
          }

          const currentAssistantId = assistantIdRef.current;
          setMessages((prev) => {
            const updated = prev.slice();
            const last = updated[updated.length - 1];
            if (last && last.id === currentAssistantId) {
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

  const retry = useCallback(() => {
    if (lastUserMessageRef.current) {
      send(lastUserMessageRef.current);
    }
  }, [send]);

  const resetConversation = useCallback(() => {
    abortControllerRef.current?.abort();
    setMessages([]);
    setStreaming(false);
    assistantIdRef.current = null;
    abortControllerRef.current = null;
    lastUserMessageRef.current = null;
    nextIdRef.current = 1;
    setConversationVersion((v) => v + 1);
  }, []);

  return (
    <ConversationContext.Provider value={{ messages, streaming, conversationVersion, send, retry, resetConversation }}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversation(): ConversationContextValue {
  const ctx = useContext(ConversationContext);
  if (!ctx) throw new Error("useConversation must be used within ConversationProvider");
  return ctx;
}

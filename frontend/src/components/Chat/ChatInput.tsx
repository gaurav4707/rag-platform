import { useRef, useCallback, useEffect } from "react";
import { Button } from "../ui";
import { useConversation } from "../../context/ConversationContext";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const MAX_VISIBLE_LINES = 6;
const LINE_HEIGHT = 24;

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { conversationVersion } = useConversation();
  const prevVersionRef = useRef(conversationVersion);

  useEffect(() => {
    if (conversationVersion !== prevVersionRef.current) {
      prevVersionRef.current = conversationVersion;
      const el = textareaRef.current;
      if (el) {
        el.value = "";
        el.style.height = "auto";
        el.focus();
      }
    }
  }, [conversationVersion]);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, MAX_VISIBLE_LINES * LINE_HEIGHT) + "px";
  }, []);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const el = textareaRef.current;
    if (!el) return;
    const text = el.value.trim();
    if (!text) return;
    onSend(text);
    el.value = "";
    el.style.height = "auto";
    el.focus();
  }

  return (
    <div className="flex-shrink-0 border-t border-surface-200 bg-white px-4 py-3 lg:px-6 lg:py-4">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex items-end gap-2.5 rounded-xl border border-surface-300 bg-surface-50 px-3 py-2.5 transition-all duration-150 focus-within:border-accent-400 focus-within:bg-white focus-within:shadow-focus">
          <textarea
            ref={textareaRef}
            name="message"
            rows={1}
            placeholder="Ask a question about your documents..."
            disabled={disabled}
            onInput={autoResize}
            onKeyDown={handleKeyDown}
            className="min-h-[24px] flex-1 resize-none bg-transparent text-sm leading-6 text-surface-800 placeholder:text-surface-400 focus:outline-none disabled:opacity-50"
            aria-label="Chat message"
          />
          <Button
            type="button"
            variant="primary"
            onClick={submit}
            disabled={disabled}
            className="!h-8 !w-8 !min-w-0 !rounded-lg !p-0"
            aria-label="Send message"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 12L3.269 3.126A9.028 9.028 0 0112 3c4.97 0 9 4.03 9 9s-4.03 9-9 9-9-4.03-9-9m12 0c0-1.657-1.343-3-3-3s-3 1.343-3 3 1.343 3 3 3 3-1.343 3-3z"
              />
            </svg>
          </Button>
        </div>
        <p className="mt-1.5 px-1 text-xs text-surface-400">
          Press Enter to send, Shift+Enter for a new line
        </p>
      </div>
    </div>
  );
}

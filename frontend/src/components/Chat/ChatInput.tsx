import { useRef, useCallback } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const MAX_VISIBLE_LINES = 6;
const LINE_HEIGHT = 24;

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    <div className="border-t border-gray-200 bg-white px-3 py-3 lg:px-6 lg:py-4">
      <div className="flex gap-2">
        <textarea
          ref={textareaRef}
          name="message"
          rows={1}
          placeholder="Ask a question..."
          disabled={disabled}
          onInput={autoResize}
          onKeyDown={handleKeyDown}
          className="min-h-[44px] flex-1 resize-none rounded-md border border-gray-300 px-3 py-2.5 text-sm leading-6 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
          aria-label="Chat message"
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled}
          className="min-h-[44px] self-end rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          aria-label="Send message"
        >
          Send
        </button>
      </div>
    </div>
  );
}

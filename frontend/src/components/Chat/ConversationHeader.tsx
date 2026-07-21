import { useConversation } from "../../context/ConversationContext";
import { Button } from "../ui";

interface ConversationHeaderProps {
  onNewChat: () => void;
}

export function ConversationHeader({ onNewChat }: ConversationHeaderProps) {
  const { messages } = useConversation();
  const count = messages.length;

  return (
    <div className="mb-4 flex items-center justify-between">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-surface-500">
          Conversation
        </h3>
        <p className="mt-0.5 text-xs text-surface-400">
          {count} {count === 1 ? "message" : "messages"}
        </p>
      </div>
      <div className="flex gap-2">
        <Button variant="secondary" onClick={onNewChat}>
          New Chat
        </Button>
      </div>
    </div>
  );
}

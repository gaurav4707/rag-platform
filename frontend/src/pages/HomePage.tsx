import { useState, useCallback } from "react";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { ChatInput } from "../components/Chat/ChatInput";
import { ConfirmationDialog } from "../components/Common";
import { useConversation } from "../context/ConversationContext";
import { useSettings } from "../context/SettingsContext";

export function HomePage() {
  const { send, streaming, resetConversation } = useConversation();
  const { settings } = useSettings();
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  const requestReset = useCallback(() => {
    if (settings.general.confirmBeforeDelete) {
      setResetDialogOpen(true);
    } else {
      resetConversation();
    }
  }, [settings.general.confirmBeforeDelete, resetConversation]);

  function handleConfirmReset() {
    setResetDialogOpen(false);
    resetConversation();
  }

  function handleCancelReset() {
    setResetDialogOpen(false);
  }

  return (
    <>
      <ChatWindow onNewChat={requestReset} />
      <ChatInput onSend={send} disabled={streaming} />

      <ConfirmationDialog
        isOpen={resetDialogOpen}
        title="Start new conversation?"
        message="This will clear all current messages. Uploaded documents will be preserved."
        confirmLabel="Start New"
        cancelLabel="Cancel"
        variant="primary"
        onConfirm={handleConfirmReset}
        onCancel={handleCancelReset}
      />
    </>
  );
}

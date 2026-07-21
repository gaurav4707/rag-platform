import { BASE_URL } from "./api";
import type { StreamCallbacks, Source } from "../types";

export async function streamMessage(
  message: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const { onToken, onDone, onError } = callbacks;

  try {
    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Stream request failed with status ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      if (signal?.aborted) {
        throw new DOMException("Aborted", "AbortError");
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const raw = line.slice(6);
          try {
            const parsed = JSON.parse(raw);
            if (typeof parsed.token === "string") {
              onToken(parsed.token);
            } else if (parsed.done === true) {
              onDone(
                parsed.sources as Source[],
                parsed.tool_calls as Record<string, unknown>[],
              );
            }
          } catch {
            // skip non-JSON lines
          }
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return;
    }
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

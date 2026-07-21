export interface ChatRequest {
  message: string;
}

export interface Source {
  document: string;
  page: number | null;
  document_id: string;
  score: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  tool_calls: Record<string, unknown>[] | null;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
  already_indexed?: boolean;
}

export interface Document {
  document_id: string;
  filename: string;
  status: string;
}

export type MessageState = "pending" | "streaming" | "complete" | "interrupted" | "error";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  state?: MessageState;
  sources?: Source[];
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onDone: (sources: Source[], toolCalls: Record<string, unknown>[]) => void;
  onError: (error: Error) => void;
}

export type UploadStatus = "idle" | "uploading" | "processing" | "success" | "error";

export interface UploadLifecycle {
  onProgress?: (progress: number) => void;
  onProcessing?: () => void;
}

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

export interface DeleteResponse {
  status: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
  streamInterrupted?: boolean;
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onDone: (sources: Source[], toolCalls: Record<string, unknown>[]) => void;
  onError: (error: Error) => void;
}

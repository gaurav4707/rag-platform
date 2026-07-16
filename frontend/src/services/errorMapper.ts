import { ApiError } from "./api";

export interface UserFriendlyError {
  title: string;
  description: string;
  actionLabel?: string;
  action?: () => void;
}

const ERROR_MESSAGES: Record<string, { title: string; description: string }> = {
  INVALID_FILE: {
    title: "Invalid File",
    description: "Only PDF documents are supported.",
  },
  EMPTY_PDF: {
    title: "Empty PDF",
    description: "The uploaded PDF contains no readable text.",
  },
  CORRUPTED_PDF: {
    title: "Invalid PDF",
    description: "The file appears to be corrupted or unreadable.",
  },
  FILE_TOO_LARGE: {
    title: "File Too Large",
    description: "Choose a smaller PDF.",
  },
  DOCUMENT_ALREADY_EXISTS: {
    title: "Document Already Exists",
    description: "This PDF has already been uploaded.",
  },
  DOCUMENT_NOT_FOUND: {
    title: "Document Not Found",
    description: "The document may have been deleted.",
  },
  INDEXING_FAILED: {
    title: "Document Processing Failed",
    description: "The document could not be indexed.",
  },
  NETWORK_ERROR: {
    title: "Connection Lost",
    description: "Unable to reach the server.",
  },
  VECTOR_STORE_ERROR: {
    title: "Search Unavailable",
    description: "The search index is temporarily unavailable.",
  },
  INTERNAL_SERVER_ERROR: {
    title: "Something Went Wrong",
    description: "Please try again in a moment.",
  },
};

const DEFAULT_ERROR: { title: string; description: string } = {
  title: "Something Went Wrong",
  description: "Please try again.",
};

function detectSpecificError(message: string): { title: string; description: string } | null {
  const msg = message.toLowerCase();
  if (msg.includes("embeddings to be non-empty") || msg.includes("non-empty list or numpy array") || msg.includes("pdf contains no extractable text")) {
    return {
      title: "Empty PDF",
      description: "The uploaded PDF contains no readable text.",
    };
  }
  if (msg.includes("too large") || msg.includes("file size")) {
    return {
      title: "File Too Large",
      description: "Choose a smaller PDF.",
    };
  }
  if (msg.includes("corrupt") || msg.includes("invalid pdf") || msg.includes("unreadable")) {
    return {
      title: "Invalid PDF",
      description: "The file appears to be corrupted or unreadable.",
    };
  }
  return null;
}

export function mapApiError(error: ApiError | Error): UserFriendlyError {
  if (error instanceof ApiError) {
    const specific = detectSpecificError(error.message);
    if (specific) return specific;

    const mapped = ERROR_MESSAGES[error.code] || DEFAULT_ERROR;
    return {
      title: mapped.title,
      description: mapped.description,
    };
  }

  return DEFAULT_ERROR;
}

export function getErrorTitle(error: ApiError | Error): string {
  return mapApiError(error).title;
}

export function getErrorDescription(error: ApiError | Error): string {
  return mapApiError(error).description;
}

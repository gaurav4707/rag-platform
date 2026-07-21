import type { Settings } from "../types/settings";

const STORAGE_KEY = "rag-agent-settings";

export const DEFAULT_SETTINGS: Settings = {
  general: {
    confirmBeforeDelete: true,
  },
  retrieval: {
    showCitations: true,
  },
};

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS };
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(settings: Settings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function resetSettings(): Settings {
  localStorage.removeItem(STORAGE_KEY);
  return { ...DEFAULT_SETTINGS };
}

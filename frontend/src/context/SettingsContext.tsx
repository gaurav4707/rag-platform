import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { Settings } from "../types/settings";
import { loadSettings, saveSettings, resetSettings } from "../services/settingsService";

interface SettingsContextValue {
  settings: Settings;
  updateSettings: (payload: Partial<Settings>) => void;
  resetToDefaults: () => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(loadSettings);

  const updateSettings = useCallback((payload: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...payload };
      saveSettings(next);
      return next;
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    const defaults = resetSettings();
    setSettings(defaults);
  }, []);

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetToDefaults }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}

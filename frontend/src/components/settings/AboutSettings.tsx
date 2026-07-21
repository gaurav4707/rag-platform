import { useSettings } from "../../context/SettingsContext";
import { SectionTitle } from "../ui/SectionTitle";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";

export function AboutSettings() {
  const { resetToDefaults } = useSettings();

  return (
    <div>
      <SectionTitle title="About" />
      <Card padding={false}>
        <div className="space-y-1 px-4 py-3 text-sm text-surface-600">
          <p>RAG Agent</p>
          <p className="text-xs text-surface-400">v1.0.0</p>
        </div>
        <div className="border-t border-surface-100 px-4 py-3">
          <Button variant="danger" onClick={resetToDefaults}>
            Reset all settings to defaults
          </Button>
        </div>
      </Card>
    </div>
  );
}

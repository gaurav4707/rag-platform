import { useSettings } from "../../context/SettingsContext";
import { SectionTitle } from "../ui/SectionTitle";
import { Card } from "../ui/Card";

export function RetrievalSettings() {
  const { settings, updateSettings } = useSettings();
  const checked = settings.retrieval.showCitations;

  function handleToggle() {
    updateSettings({
      retrieval: { ...settings.retrieval, showCitations: !checked },
    });
  }

  return (
    <div>
      <SectionTitle title="Retrieval" />
      <Card padding={false}>
        <label className="flex cursor-pointer items-center gap-3 px-4 py-3 text-sm">
          <input
            type="checkbox"
            checked={checked}
            onChange={handleToggle}
            className="h-4 w-4 rounded border-surface-300 text-accent-600 focus:ring-accent-500"
          />
          <span className="flex-1 text-surface-700">
            Show source citations in responses
          </span>
        </label>
      </Card>
    </div>
  );
}

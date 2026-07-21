import { PageContainer } from "../components/ui/PageContainer";
import { GeneralSettings } from "../components/settings/GeneralSettings";
import { RetrievalSettings } from "../components/settings/RetrievalSettings";
import { AboutSettings } from "../components/settings/AboutSettings";

export function SettingsPage() {
  return (
    <PageContainer>
      <div className="mx-auto max-w-lg space-y-8 py-8">
        <h2 className="text-lg font-semibold tracking-tight text-surface-900">
          Settings
        </h2>
        <GeneralSettings />
        <RetrievalSettings />
        <AboutSettings />
      </div>
    </PageContainer>
  );
}

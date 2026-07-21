import { useState } from "react";
import { MainLayout } from "./components/Layout/MainLayout";
import { Sidebar } from "./components/Layout/Sidebar";
import { HomePage } from "./pages/HomePage";
import { SettingsPage } from "./pages/SettingsPage";
import { ToastProvider, ToastContainer } from "./components/Common";
import { SettingsProvider } from "./context/SettingsContext";

type Page = "home" | "settings";

export function App() {
  const [page, setPage] = useState<Page>("home");

  return (
    <SettingsProvider>
      <ToastProvider>
        <>
          <MainLayout
            sidebar={<Sidebar />}
            onNavigate={setPage}
            currentPage={page}
          >
            {page === "home" ? <HomePage /> : <SettingsPage />}
          </MainLayout>
          <ToastContainer />
        </>
      </ToastProvider>
    </SettingsProvider>
  );
}

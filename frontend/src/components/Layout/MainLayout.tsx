import type { ReactNode } from "react";
import { Header } from "./Header";

type Page = "home" | "settings";

interface MainLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
  onNavigate: (page: Page) => void;
  currentPage: Page;
}

export function MainLayout({ sidebar, children, onNavigate, currentPage }: MainLayoutProps) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-surface-50">
      <Header onNavigate={onNavigate} currentPage={currentPage} />

      <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
        {sidebar}

        <main className="flex flex-1 flex-col overflow-hidden bg-surface-50">
          {children}
        </main>
      </div>
    </div>
  );
}

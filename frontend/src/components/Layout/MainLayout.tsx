import type { ReactNode } from "react";
import { Header } from "./Header";

interface MainLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function MainLayout({ sidebar, children }: MainLayoutProps) {
  return (
    <div className="flex h-screen flex-col">
      <Header />

      <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
        {sidebar}

        <main className="flex flex-1 flex-col overflow-hidden bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  );
}

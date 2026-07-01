import { MainLayout } from "./components/Layout/MainLayout";
import { Sidebar } from "./components/Layout/Sidebar";
import { HomePage } from "./pages/HomePage";

export function App() {
  return (
    <MainLayout sidebar={<Sidebar />}>
      <HomePage />
    </MainLayout>
  );
}

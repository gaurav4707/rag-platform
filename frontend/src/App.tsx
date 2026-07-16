import { MainLayout } from "./components/Layout/MainLayout";
import { Sidebar } from "./components/Layout/Sidebar";
import { HomePage } from "./pages/HomePage";
import { ToastProvider, ToastContainer } from "./components/Common";

export function App() {
  return (
    <ToastProvider>
      <>
        <MainLayout sidebar={<Sidebar />}>
          <HomePage />
        </MainLayout>
        <ToastContainer />
      </>
    </ToastProvider>
  );
}

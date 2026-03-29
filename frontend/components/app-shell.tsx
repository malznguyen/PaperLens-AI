import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen md:grid md:grid-cols-[280px_minmax(0,1fr)]">
      <Sidebar />
      <div className="relative min-w-0">
        <TopBar />
        <main className="mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-7xl flex-col px-4 pb-8 pt-4 md:px-8 md:pt-6">
          {children}
        </main>
      </div>
    </div>
  );
}

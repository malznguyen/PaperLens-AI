import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen md:grid md:grid-cols-[260px_minmax(0,1fr)]">
      <Sidebar />
      <div className="relative min-w-0">
        <TopBar />
        <main className="mx-auto flex min-h-[calc(100vh-84px)] w-full max-w-[1500px] flex-col px-4 pb-10 pt-5 sm:px-5 md:px-7 md:pt-6 xl:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}

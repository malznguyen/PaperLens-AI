"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navigationItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-[color:var(--line)] bg-[color:var(--sidebar)]/85 backdrop-blur md:sticky md:top-0 md:flex md:h-screen md:flex-col md:border-b-0 md:border-r">
      <div className="px-4 pb-4 pt-5 md:px-5 md:pb-5 md:pt-6">
        <div className="rounded-[1.8rem] border border-[color:var(--line)] bg-white/72 p-4 shadow-panel md:p-5">
          <p className="text-[11px] uppercase tracking-[0.28em] text-[color:var(--muted)]">
            PaperLens AI
          </p>
          <h1 className="mt-3 text-[2rem] text-slate-900 md:text-[2.2rem]">Research workspace</h1>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
            Discover, ingest, analyze, and compare papers with a workflow-first interface.
          </p>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-4 md:flex-1 md:flex-col md:px-5">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "min-w-[180px] rounded-[1.2rem] border px-3.5 py-3 transition md:min-w-0",
                isActive
                  ? "border-[color:var(--accent)]/24 bg-[color:var(--accent-soft)]/92 text-slate-900 shadow-sm"
                  : "border-[color:var(--line)] bg-white/58 text-[color:var(--muted)] hover:bg-white/82 hover:text-slate-900",
              )}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-[color:var(--line)] bg-white/82 p-2">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium leading-5">{item.title}</p>
                  <p className="text-xs leading-5">{item.description}</p>
                </div>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="hidden px-5 pb-5 md:block">
        <div className="rounded-[1.8rem] border border-white/10 bg-[#13212d] p-5 text-slate-100 shadow-panel">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-300">Tech stack</p>
          <ul className="mt-4 space-y-2 text-sm text-slate-200">
            <li>FastAPI + Python backend</li>
            <li>Next.js + React frontend</li>
            <li>Chroma vector store</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}

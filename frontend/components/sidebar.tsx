"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navigationItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-black/10 bg-[color:var(--sidebar)]/80 backdrop-blur md:sticky md:top-0 md:flex md:h-screen md:flex-col md:border-b-0 md:border-r">
      <div className="px-5 pb-4 pt-6 md:px-6">
        <div className="rounded-3xl border border-black/10 bg-white/70 p-5 shadow-panel">
          <p className="text-xs uppercase tracking-[0.26em] text-[color:var(--muted)]">PaperLens AI</p>
          <h1 className="mt-3 text-3xl text-slate-900">Research workspace</h1>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
            Discover, ingest, analyze, and compare papers with a workflow-first interface.
          </p>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-4 md:flex-1 md:flex-col md:px-6">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "min-w-[220px] rounded-2xl border px-4 py-3 transition md:min-w-0",
                isActive
                  ? "border-[color:var(--accent)]/30 bg-[color:var(--accent-soft)] text-slate-900"
                  : "border-black/10 bg-white/55 text-[color:var(--muted)] hover:bg-white/80 hover:text-slate-900",
              )}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-black/10 bg-white/75 p-2">
                  <Icon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs">{item.description}</p>
                </div>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="hidden px-6 pb-6 md:block">
        <div className="rounded-3xl border border-black/10 bg-[#13212d] p-5 text-slate-100 shadow-panel">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-300">Phase 1 stack</p>
          <ul className="mt-4 space-y-2 text-sm text-slate-200">
            <li>FastAPI backend scaffold</li>
            <li>Next.js dashboard shell</li>
            <li>Chroma-ready local data layout</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}

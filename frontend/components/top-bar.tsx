import { CalendarDays, ShieldCheck } from "lucide-react";

import { StatusChip } from "@/components/status-chip";

const today = new Intl.DateTimeFormat("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
  year: "numeric",
}).format(new Date());

export function TopBar() {
  return (
    <header className="sticky top-0 z-20 border-b border-[color:var(--line)] bg-[color:var(--panel)]/92 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-3 px-4 py-3 sm:px-5 md:flex-row md:items-center md:justify-between md:px-7 xl:px-8">
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-[color:var(--muted)]">
            PaperLens AI
          </p>
          <h2 className="mt-1 text-[1.7rem] text-slate-900">Research workflow dashboard</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm text-[color:var(--muted)]">
          <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/82 px-3 py-1.5">
            <CalendarDays className="h-4 w-4" />
            <span>{today}</span>
          </div>
          <StatusChip tone="positive">
            <ShieldCheck className="mr-2 h-3.5 w-3.5" />
            Local-first pipeline
          </StatusChip>
        </div>
      </div>
    </header>
  );
}

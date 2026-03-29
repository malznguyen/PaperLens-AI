import { SearchX } from "lucide-react";

import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description: string;
  compact?: boolean;
};

export function EmptyState({
  title,
  description,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "rounded-[1.6rem] border border-dashed border-[color:var(--line)] bg-white/78 text-center",
        compact ? "px-4 py-4" : "px-6 py-10",
      )}
    >
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[color:var(--line)] bg-[color:var(--accent-soft)] text-[color:var(--accent)]">
        <SearchX className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-[1.55rem] text-slate-900">{title}</h3>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-[color:var(--muted)]">
        {description}
      </p>
    </div>
  );
}

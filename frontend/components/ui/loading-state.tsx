import { LoaderCircle } from "lucide-react";

import { cn } from "@/lib/utils";

type LoadingStateProps = {
  title: string;
  description: string;
  compact?: boolean;
};

export function LoadingState({
  title,
  description,
  compact = false,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "rounded-[1.6rem] border border-black/10 bg-white/76",
        compact ? "px-4 py-4" : "px-6 py-10",
      )}
    >
      <div className={cn("flex gap-4", compact ? "items-start" : "flex-col items-center text-center")}>
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] text-[color:var(--accent)]">
          <LoaderCircle className="h-5 w-5 animate-spin" />
        </div>
        <div>
          <h3 className="text-xl text-slate-900">{title}</h3>
          <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{description}</p>
        </div>
      </div>
    </div>
  );
}

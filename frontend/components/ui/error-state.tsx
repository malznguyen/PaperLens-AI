import { AlertTriangle } from "lucide-react";

import { cn } from "@/lib/utils";

type ErrorStateProps = {
  title: string;
  description: string;
  compact?: boolean;
};

export function ErrorState({
  title,
  description,
  compact = false,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "rounded-[1.6rem] border border-[#d9b8ab] bg-[#fff5f1]",
        compact ? "px-4 py-4" : "px-6 py-10",
      )}
    >
      <div className={cn("flex gap-4", compact ? "items-start" : "flex-col items-center text-center")}>
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-[#e4c7bb] bg-white/80 text-[#a04b35]">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-xl text-slate-900">{title}</h3>
          <p className="mt-2 text-sm leading-6 text-[#7d5144]">{description}</p>
        </div>
      </div>
    </div>
  );
}

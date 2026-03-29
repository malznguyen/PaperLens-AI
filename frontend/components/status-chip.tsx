import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const statusChipVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em]",
  {
    variants: {
      tone: {
        neutral: "border-black/10 bg-white/80 text-slate-700",
        positive: "border-[color:var(--success)]/20 bg-[color:var(--success)]/10 text-[color:var(--success)]",
        warning: "border-[color:var(--warning)]/20 bg-[color:var(--warning)]/10 text-[color:var(--warning)]",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  },
);

type StatusChipProps = React.HTMLAttributes<HTMLSpanElement> &
  VariantProps<typeof statusChipVariants>;

export function StatusChip({ className, tone, ...props }: StatusChipProps) {
  return <span className={cn(statusChipVariants({ tone }), className)} {...props} />;
}

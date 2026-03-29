import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const statusChipVariants = cva(
  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.16em]",
  {
    variants: {
      tone: {
        neutral: "border-[color:var(--line)] bg-white/86 text-slate-700",
        positive:
          "border-[color:var(--success)]/20 bg-[color:var(--success)]/10 text-[color:var(--success)]",
        warning:
          "border-[color:var(--warning)]/22 bg-[color:var(--warning)]/10 text-[color:var(--warning)]",
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

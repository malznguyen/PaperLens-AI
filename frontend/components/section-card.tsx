import { cn } from "@/lib/utils";

type SectionCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
  className?: string;
};

export function SectionCard({
  eyebrow,
  title,
  description,
  children,
  className,
}: SectionCardProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-[1.85rem] border border-[color:var(--line)] bg-[color:var(--panel)]/95 p-5 shadow-panel sm:p-6 lg:p-7",
        className,
      )}
    >
      <div className="space-y-3">
        <p className="text-[11px] uppercase tracking-[0.28em] text-[color:var(--muted)]">
          {eyebrow}
        </p>
        <h2 className="max-w-4xl text-[1.95rem] text-slate-900 sm:text-[2.15rem]">{title}</h2>
        <p className="max-w-3xl text-sm leading-6 text-[color:var(--muted-strong)]">
          {description}
        </p>
      </div>
      <div className="mt-6">{children}</div>
    </section>
  );
}

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
    <section className={cn("rounded-[1.75rem] border border-black/10 bg-[color:var(--panel)] p-6 shadow-panel", className)}>
      <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">{eyebrow}</p>
      <h2 className="mt-3 text-3xl text-slate-900">{title}</h2>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-[color:var(--muted)]">{description}</p>
      <div className="mt-6">{children}</div>
    </section>
  );
}

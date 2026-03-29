type WorkflowCardProps = {
  step: number;
  title: string;
  description: string;
};

export function WorkflowCard({ step, title, description }: WorkflowCardProps) {
  return (
    <article className="rounded-3xl border border-black/10 bg-white/80 p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">Step 0{step}</p>
        <span className="rounded-full border border-black/10 px-3 py-1 text-xs text-[color:var(--muted)]">
          {title}
        </span>
      </div>
      <h3 className="mt-4 text-2xl text-slate-900">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{description}</p>
    </article>
  );
}

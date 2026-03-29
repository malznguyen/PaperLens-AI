type WorkflowCardProps = {
  step: number;
  title: string;
  description: string;
};

export function WorkflowCard({ step, title, description }: WorkflowCardProps) {
  return (
    <article className="rounded-[1.6rem] border border-[color:var(--line)] bg-white/84 p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">Step 0{step}</p>
        <span className="h-px w-12 bg-[color:var(--line-strong)]" />
      </div>
      <h3 className="mt-4 text-[1.45rem] text-slate-900">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{description}</p>
    </article>
  );
}

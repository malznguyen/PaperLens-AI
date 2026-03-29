import { EmptyState } from "@/components/ui/empty-state";
import type { ChatCitation, ComparisonRow } from "@/lib/api";

type ComparisonTableProps = {
  rows: ComparisonRow[];
  citations?: ChatCitation[];
};

const columns: Array<{ key: keyof ComparisonRow; label: string }> = [
  { key: "paper_title", label: "Paper" },
  { key: "objective", label: "Objective" },
  { key: "methodology", label: "Methodology" },
  { key: "dataset", label: "Dataset" },
  { key: "strengths", label: "Strengths" },
  { key: "limitations", label: "Limitations" },
  { key: "key_contribution", label: "Key contribution" },
];

function getCitationsForPaper(paperId: string, citations: ChatCitation[]): ChatCitation[] {
  return citations.filter((c) => c.paper_id === paperId);
}

export function ComparisonTable({ rows, citations = [] }: ComparisonTableProps) {
  if (rows.length === 0) {
    return (
      <EmptyState
        compact
        title="No comparison rows returned"
        description="The comparison workflow did not return any structured paper rows for this request."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3 2xl:hidden">
        {rows.map((row) => {
          const paperCitations = getCitationsForPaper(row.paper_id, citations);

          return (
            <article
              key={row.paper_id}
              className="rounded-[1.6rem] border border-[color:var(--line)] bg-white/82 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[color:var(--muted)]">
                    {row.paper_id}
                  </p>
                  <h4 className="mt-2 text-[1.35rem] leading-tight text-slate-900">
                    {row.paper_title}
                  </h4>
                </div>

                {paperCitations.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {paperCitations.map((c) => (
                      <a
                        key={c.chunk_id}
                        href={c.source_url}
                        target="_blank"
                        rel="noreferrer"
                        title={`${c.paper_title} - Page ${c.page_number}`}
                        className="inline-flex items-center rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)] px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.14em] text-[color:var(--accent)] transition hover:bg-[color:var(--accent)]/20"
                      >
                        {c.label} p.{c.page_number}
                      </a>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {columns
                  .filter((column) => column.key !== "paper_title")
                  .map((column) => (
                    <div
                      key={`${row.paper_id}-${column.key}`}
                      className="rounded-[1.25rem] border border-[color:var(--line)] bg-[#f6f0e7] p-4"
                    >
                      <dt className="text-[11px] uppercase tracking-[0.2em] text-[color:var(--muted)]">
                        {column.label}
                      </dt>
                      <dd className="mt-2 text-sm leading-6 text-slate-800">
                        {row[column.key]}
                      </dd>
                    </div>
                  ))}
              </div>
            </article>
          );
        })}
      </div>

      <div className="hidden overflow-x-auto rounded-[1.6rem] border border-[color:var(--line)] bg-white/82 2xl:block">
        <table className="min-w-[1180px] w-full border-collapse text-left">
          <thead className="bg-[#f6f0e7]">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="border-b border-[color:var(--line)] px-4 py-3 text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)]"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const paperCitations = getCitationsForPaper(row.paper_id, citations);
              return (
                <tr key={row.paper_id} className="align-top">
                  {columns.map((column) => {
                    const cellValue = row[column.key];
                    return (
                      <td
                        key={`${row.paper_id}-${column.key}`}
                        className="border-b border-[color:var(--line)] px-4 py-4 text-sm leading-6 text-slate-800 last:border-b-0"
                      >
                        {column.key === "paper_title" ? (
                          <div>
                            <p className="font-medium text-slate-900">{row.paper_title}</p>
                            <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-[color:var(--muted)]">
                              {row.paper_id}
                            </p>
                            {paperCitations.length > 0 ? (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {paperCitations.map((c) => (
                                  <a
                                    key={c.chunk_id}
                                    href={c.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    title={`${c.paper_title} - Page ${c.page_number}`}
                                    className="inline-flex items-center rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)] px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-[color:var(--accent)] transition hover:bg-[color:var(--accent)]/20"
                                  >
                                    {c.label} p.{c.page_number}
                                  </a>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        ) : (
                          cellValue
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

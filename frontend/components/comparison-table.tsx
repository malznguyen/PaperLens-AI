import { EmptyState } from "@/components/ui/empty-state";
import type { ComparisonRow } from "@/lib/api";

type ComparisonTableProps = {
  rows: ComparisonRow[];
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

export function ComparisonTable({ rows }: ComparisonTableProps) {
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
    <div className="overflow-x-auto rounded-[1.6rem] border border-black/10 bg-white/78">
      <table className="min-w-[1120px] w-full border-collapse text-left">
        <thead className="bg-[#f6f0e7]">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="border-b border-black/10 px-4 py-3 text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.paper_id} className="align-top">
              {columns.map((column) => {
                const cellValue = row[column.key];
                return (
                  <td
                    key={`${row.paper_id}-${column.key}`}
                    className="border-b border-black/10 px-4 py-4 text-sm leading-6 text-slate-800 last:border-b-0"
                  >
                    {column.key === "paper_title" ? (
                      <div>
                        <p className="font-medium text-slate-900">{row.paper_title}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                          {row.paper_id}
                        </p>
                      </div>
                    ) : (
                      cellValue
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

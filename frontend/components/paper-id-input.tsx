"use client";

import { useState } from "react";
import { ClipboardCopy, X } from "lucide-react";

import { parsePaperIds } from "@/lib/paper-ids";

type PaperIdInputProps = {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  helperText?: string;
};

export function PaperIdInput({
  value,
  onChange,
  label = "Paper IDs",
  placeholder = "2401.12345, 2402.67890, 2403.11111",
  helperText,
}: PaperIdInputProps) {
  const [copied, setCopied] = useState(false);
  const parsedIds = parsePaperIds(value);

  function handleCopyIds() {
    if (parsedIds.length === 0) return;
    navigator.clipboard.writeText(parsedIds.join(", ")).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  function handleRemoveId(idToRemove: string) {
    const remaining = parsedIds.filter((id) => id !== idToRemove);
    onChange(remaining.join(", "));
  }

  return (
    <label className="block">
      <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-2 w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
        autoComplete="off"
      />
      {parsedIds.length > 0 ? (
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {parsedIds.map((id) => (
            <span
              key={id}
              className="inline-flex items-center gap-1 rounded-lg bg-[#f6f0e7] px-2 py-1 text-xs text-slate-700"
            >
              {id}
              <button
                type="button"
                onClick={() => handleRemoveId(id)}
                className="rounded p-0.5 text-slate-400 transition hover:text-slate-700"
                aria-label={`Remove ${id}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          <button
            type="button"
            onClick={handleCopyIds}
            className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-[color:var(--muted)] transition hover:bg-[#f6f0e7] hover:text-slate-700"
            title="Copy all IDs for use in other workflows"
          >
            <ClipboardCopy className="h-3 w-3" />
            {copied ? "Copied" : "Copy all"}
          </button>
        </div>
      ) : null}
      {helperText ? (
        <p className="mt-1.5 text-xs text-[color:var(--muted)]">{helperText}</p>
      ) : null}
    </label>
  );
}

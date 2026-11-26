"use client";

import { FormEvent, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError } from "@/lib/api";

type AIEnvelope = {
  result: {
    answer?: string;
    tools_used?: string[];
    provider?: string;
    labeled_ai?: boolean;
    tool_results?: unknown[];
  };
  explanation: string;
  sources: { type: string; id: string; label: string }[];
};

const EXAMPLES = [
  "Which products are low stock?",
  "What should I reorder?",
  "Show open purchase orders",
  "Stockout risk for SKU-009",
  "Recent movements for SKU-001",
];

export default function AiAskPage() {
  return (
    <AuthGate>
      <AskView />
    </AuthGate>
  );
}

function AskView() {
  const [question, setQuestion] = useState("Which products are low stock?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AIEnvelope | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<AIEnvelope>("/ai/inventory-question", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      setData(res);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Question failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="max-w-3xl space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">AI assistant</p>
        <h2 className="mt-2 text-3xl font-semibold">Inventory Q&amp;A</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Natural-language questions over allowlisted read tools only (org-scoped). Answers are
          labeled AI content and do not change stock or create orders.
        </p>
      </header>

      <div className="rounded border border-[var(--warn)]/40 bg-[var(--warn)]/10 px-4 py-3 text-sm">
        AI-generated content — verify against stock and PO screens before acting.
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <textarea
          className="min-h-28 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about stock, movements, open POs, or reorder candidates"
        />
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              className="rounded border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--ink)]"
              onClick={() => setQuestion(ex)}
            >
              {ex}
            </button>
          ))}
        </div>
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-40"
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      <StatusBanner error={error} />

      {data && (
        <article className="space-y-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/80 p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--warn)]">AI answer</p>
          <p className="leading-relaxed">{data.result.answer}</p>
          <p className="text-sm text-[var(--muted)]">{data.explanation}</p>
          <p className="text-xs text-[var(--muted)]">
            Provider: {data.result.provider ?? "demo"} · tools:{" "}
            {(data.result.tools_used ?? []).join(", ") || "none"}
          </p>
          {data.sources?.length > 0 && (
            <ul className="text-xs text-[var(--muted)]">
              {data.sources.map((s) => (
                <li key={`${s.type}-${s.id}`}>
                  {s.type}: {s.label}
                </li>
              ))}
            </ul>
          )}
        </article>
      )}
    </section>
  );
}

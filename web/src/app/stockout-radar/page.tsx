"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError } from "@/lib/api";

type RadarItem = {
  product_id: string;
  sku: string;
  name: string;
  risk_score: number;
  risk_level: string;
  formula: string;
  inputs: {
    on_hand: number;
    avg_daily_movement: number;
    supplier_lead_time_days: number;
    safety_stock: number;
    coverage_days: number;
  };
  reasons: string[];
  assumptions: string[];
};

type AIEnvelope = {
  result: {
    items?: RadarItem[];
    formula?: string;
    provider?: string;
    labeled_ai?: boolean;
  };
  explanation: string;
};

export default function StockoutRadarPage() {
  return (
    <AuthGate>
      <RadarView />
    </AuthGate>
  );
}

function RadarView() {
  const [items, setItems] = useState<RadarItem[]>([]);
  const [formula, setFormula] = useState("");
  const [explanation, setExplanation] = useState("");
  const [provider, setProvider] = useState("demo");
  const [selected, setSelected] = useState<RadarItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<AIEnvelope>("/ai/stockout-radar", {
        method: "POST",
        body: JSON.stringify({ lookback_days: 30, limit: 20 }),
      });
      const list = res.result.items ?? [];
      setItems(list);
      setFormula(res.result.formula ?? list[0]?.formula ?? "");
      setExplanation(res.explanation);
      setProvider(res.result.provider ?? "demo");
      setSelected(list[0] ?? null);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load Stockout Radar");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="max-w-5xl space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Differentiator</p>
        <h2 className="mt-2 text-3xl font-semibold">Stockout Radar</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Transparent risk scores from on-hand stock, average daily movement, supplier lead time,
          and safety stock. This is a risk signal — not a prediction that a stockout will occur.
        </p>
      </header>

      <div className="rounded border border-[var(--warn)]/40 bg-[var(--warn)]/10 px-4 py-3 text-sm">
        AI-labeled narration may accompany scores. Numeric risk is deterministic code.
      </div>

      <button
        type="button"
        onClick={() => void load()}
        className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)]"
      >
        Refresh radar
      </button>

      <StatusBanner error={error} />
      {loading && <p className="text-sm text-[var(--muted)]">Computing risk scores…</p>}
      {!loading && !error && items.length === 0 ? (
        <EmptyState title="No radar items" description="Seeded stock signals may be empty." />
      ) : null}

      {formula && (
        <div className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3 font-mono text-xs leading-relaxed text-[var(--muted)]">
          {formula}
        </div>
      )}

      {explanation && (
        <p className="text-sm text-[var(--muted)]">
          <span className="text-[var(--ink)]">Explanation:</span> {explanation} · provider:{" "}
          {provider}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="overflow-x-auto rounded border border-[var(--border)]">
          <table className="w-full text-sm">
            <thead className="bg-[var(--surface)] text-left text-[var(--muted)]">
              <tr>
                <th className="px-3 py-2">SKU</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Level</th>
                <th className="px-3 py-2">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.product_id}
                  className={`cursor-pointer border-t border-[var(--border)] ${
                    selected?.product_id === item.product_id ? "bg-[var(--surface)]" : ""
                  }`}
                  onClick={() => setSelected(item)}
                >
                  <td className="px-3 py-2">
                    <div className="font-medium">{item.sku}</div>
                    <div className="text-xs text-[var(--muted)]">{item.name}</div>
                  </td>
                  <td className="px-3 py-2 font-medium">{item.risk_score}</td>
                  <td className="px-3 py-2 capitalize">{item.risk_level}</td>
                  <td className="px-3 py-2">{item.inputs.coverage_days}d</td>
                </tr>
              ))}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-[var(--muted)]">
                    No radar rows available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {selected && (
          <aside className="space-y-4 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/80 p-4 text-sm">
            <h3 className="text-lg font-semibold">
              {selected.sku} · {selected.risk_score}
            </h3>
            <dl className="grid grid-cols-2 gap-2 text-[var(--muted)]">
              <div>
                <dt>On hand</dt>
                <dd className="text-[var(--ink)]">{selected.inputs.on_hand}</dd>
              </div>
              <div>
                <dt>Avg daily</dt>
                <dd className="text-[var(--ink)]">{selected.inputs.avg_daily_movement}</dd>
              </div>
              <div>
                <dt>Lead time</dt>
                <dd className="text-[var(--ink)]">{selected.inputs.supplier_lead_time_days}d</dd>
              </div>
              <div>
                <dt>Safety stock</dt>
                <dd className="text-[var(--ink)]">{selected.inputs.safety_stock}</dd>
              </div>
            </dl>
            <div>
              <p className="font-medium">Reasons</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-[var(--muted)]">
                {selected.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="font-medium">Assumptions</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-[var(--muted)]">
                {selected.assumptions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </div>
            <p className="text-xs text-[var(--warn)]">
              No certainty claims — treat this as a prioritization signal only.
            </p>
          </aside>
        )}
      </div>
    </section>
  );
}

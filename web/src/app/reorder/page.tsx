"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError } from "@/lib/api";

type ReorderLine = {
  product_id: string;
  sku: string;
  name: string;
  on_hand: string;
  avg_daily_movement: string;
  lead_time_days: number;
  reorder_point: string;
  safety_stock: string;
  recommended_qty: string;
  below_reorder_point: boolean;
  assumptions: string[];
};

type AIEnvelope = {
  result: {
    recommendations?: ReorderLine[];
    provider?: string;
    labeled_ai?: boolean;
    purchase_order_id?: string;
    po_number?: string;
    status?: string;
    stock_changed?: boolean;
  };
  explanation: string;
  sources: { type: string; id: string; label: string }[];
  requires_confirmation: boolean;
};

export default function ReorderPage() {
  return (
    <AuthGate>
      <ReorderView />
    </AuthGate>
  );
}

function ReorderView() {
  const [data, setData] = useState<AIEnvelope | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch<AIEnvelope>("/ai/reorder-recommendations", {
        method: "POST",
        body: JSON.stringify({ only_actionable: true, lookback_days: 30, limit: 25 }),
      });
      setData(res);
      const next: Record<string, boolean> = {};
      for (const line of res.result.recommendations ?? []) {
        next[line.product_id] = Number(line.recommended_qty) > 0;
      }
      setSelected(next);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function confirmDraft() {
    if (!data?.result.recommendations) return;
    const lines = data.result.recommendations
      .filter((r) => selected[r.product_id] && Number(r.recommended_qty) > 0)
      .map((r) => ({ product_id: r.product_id, quantity: r.recommended_qty }));
    if (!lines.length) {
      setError("Select at least one recommendation with quantity > 0");
      return;
    }
    const ok = window.confirm(
      `Create a DRAFT purchase order for ${lines.length} line(s)? Stock will not change.`,
    );
    if (!ok) return;

    setConfirming(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch<AIEnvelope>("/ai/confirm-draft-po", {
        method: "POST",
        body: JSON.stringify({ confirm: true, lines }),
      });
      setSuccess(
        `Draft PO ${res.result.po_number} created (status ${res.result.status}). Stock unchanged.`,
      );
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to create draft PO");
    } finally {
      setConfirming(false);
    }
  }

  const recommendations = data?.result.recommendations ?? [];

  return (
    <section className="max-w-5xl space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">AI assistant</p>
        <h2 className="mt-2 text-3xl font-semibold">Reorder recommendations</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Quantities come from on-hand stock, average daily outbound movement, lead time, and
          reorder point. AI explains assumptions — it never changes stock. Draft PO requires your
          confirmation.
        </p>
      </header>

      <div className="rounded border border-[var(--warn)]/40 bg-[var(--warn)]/10 px-4 py-3 text-sm">
        AI-generated content — review before any purchasing action.
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)]"
        >
          Refresh
        </button>
        <button
          type="button"
          disabled={confirming || !recommendations.length}
          onClick={() => void confirmDraft()}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-40"
        >
          {confirming ? "Creating draft…" : "Confirm draft PO"}
        </button>
      </div>

      <StatusBanner error={error} success={success} />
      {loading && <p className="text-sm text-[var(--muted)]">Loading recommendations…</p>}
      {!loading && !error && recommendations.length === 0 ? (
        <EmptyState
          title="No actionable reorder candidates"
          description="Stock may already be above reorder points."
        />
      ) : null}

      {data && (
        <div className="space-y-2 text-sm text-[var(--muted)]">
          <p>
            <span className="text-[var(--ink)]">Explanation:</span> {data.explanation}
          </p>
          <p>Provider: {data.result.provider ?? "demo"} · requires confirmation: yes</p>
        </div>
      )}

      <div className="overflow-x-auto rounded border border-[var(--border)]">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] text-left text-[var(--muted)]">
            <tr>
              <th className="px-3 py-2">Use</th>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">On hand</th>
              <th className="px-3 py-2">Avg/day</th>
              <th className="px-3 py-2">Lead</th>
              <th className="px-3 py-2">ROP</th>
              <th className="px-3 py-2">Qty</th>
            </tr>
          </thead>
          <tbody>
            {!loading && recommendations.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-[var(--muted)]">
                  No actionable reorder candidates right now.
                </td>
              </tr>
            )}
            {recommendations.map((line) => (
              <tr key={line.product_id} className="border-t border-[var(--border)]">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={!!selected[line.product_id]}
                    onChange={(e) =>
                      setSelected((s) => ({ ...s, [line.product_id]: e.target.checked }))
                    }
                  />
                </td>
                <td className="px-3 py-2">
                  <div className="font-medium">{line.sku}</div>
                  <div className="text-xs text-[var(--muted)]">{line.name}</div>
                  {line.below_reorder_point && (
                    <div className="text-xs text-[var(--warn)]">Below reorder point</div>
                  )}
                </td>
                <td className="px-3 py-2">{line.on_hand}</td>
                <td className="px-3 py-2">{line.avg_daily_movement}</td>
                <td className="px-3 py-2">{line.lead_time_days}d</td>
                <td className="px-3 py-2">{line.reorder_point}</td>
                <td className="px-3 py-2 font-medium text-[var(--accent)]">
                  {line.recommended_qty}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {recommendations[0]?.assumptions?.length ? (
        <div className="rounded border border-[var(--border)] bg-[var(--surface)]/50 px-4 py-3 text-sm">
          <p className="font-medium">Assumptions (sample row)</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--muted)]">
            {recommendations[0].assumptions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

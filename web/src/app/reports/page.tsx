"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import {
  apiFetch,
  ApiRequestError,
  downloadCsv,
  InventoryReport,
} from "@/lib/api";

export default function ReportsPage() {
  return (
    <AuthGate>
      <ReportsView />
    </AuthGate>
  );
}

function ReportsView() {
  const [report, setReport] = useState<InventoryReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<InventoryReport>("/reports/inventory?movement_limit=40");
      setReport(data);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load report");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function exportFile(path: string, filename: string) {
    setExporting(filename);
    setError(null);
    setSuccess(null);
    try {
      await downloadCsv(path, filename);
      setSuccess(`Downloaded ${filename}`);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "CSV export failed");
    } finally {
      setExporting(null);
    }
  }

  return (
    <section className="max-w-5xl space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Analytics</p>
          <h2 className="mt-2 text-3xl font-semibold">Inventory reports</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Deterministic stock-on-hand and movements. CSV export uses the same org-scoped data —
            no AI.
          </p>
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
            disabled={!!exporting}
            onClick={() =>
              void exportFile("/reports/inventory/stock-on-hand.csv", "stock-on-hand.csv")
            }
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-50"
          >
            {exporting === "stock-on-hand.csv" ? "Exporting…" : "CSV stock-on-hand"}
          </button>
          <button
            type="button"
            disabled={!!exporting}
            onClick={() =>
              void exportFile("/reports/inventory/movements.csv", "stock-movements.csv")
            }
            className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)] disabled:opacity-50"
          >
            {exporting === "stock-movements.csv" ? "Exporting…" : "CSV movements"}
          </button>
        </div>
      </header>

      <StatusBanner error={error} success={success} />

      {loading ? (
        <p className="text-[var(--muted)]">Loading report…</p>
      ) : !report ? (
        <EmptyState title="No report data" />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
            {[
              ["Stock value", report.stock_value],
              ["Balance rows", String(report.balance_rows)],
              ["Low stock", String(report.low_stock_items)],
              ["Pending POs", String(report.pending_purchase_orders)],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded border border-[var(--border)] bg-[var(--surface)]/50 px-3 py-3"
              >
                <p className="text-xs text-[var(--muted)]">{label}</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">{value}</p>
              </div>
            ))}
          </div>

          <div>
            <h3 className="mb-3 text-lg font-semibold">Stock on hand</h3>
            {report.stock_on_hand.length === 0 ? (
              <EmptyState title="No balances" description="Receive stock or seed the database." />
            ) : (
              <div className="overflow-x-auto rounded border border-[var(--border)]">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="bg-[var(--bg-elevated)] text-[var(--muted)]">
                    <tr>
                      <th className="px-3 py-2 font-medium">SKU</th>
                      <th className="px-3 py-2 font-medium">Location</th>
                      <th className="px-3 py-2 font-medium">Qty</th>
                      <th className="px-3 py-2 font-medium">Value</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.stock_on_hand.slice(0, 40).map((row) => (
                      <tr
                        key={`${row.sku}-${row.location_code}`}
                        className="border-t border-[var(--border)]"
                      >
                        <td className="px-3 py-2">
                          <span className="font-mono text-xs">{row.sku}</span>
                          <div className="text-[var(--muted)]">{row.name}</div>
                        </td>
                        <td className="px-3 py-2 text-[var(--muted)]">
                          {row.location_code} — {row.location_name}
                        </td>
                        <td className="px-3 py-2 tabular-nums">{row.quantity}</td>
                        <td className="px-3 py-2 tabular-nums">{row.extended_value}</td>
                        <td className="px-3 py-2">
                          {row.is_low_stock ? (
                            <span className="text-[var(--warn)]">Low</span>
                          ) : (
                            <span className="text-[var(--muted)]">OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h3 className="mb-3 text-lg font-semibold">Recent movements</h3>
            {report.recent_movements.length === 0 ? (
              <EmptyState title="No movements yet" />
            ) : (
              <div className="overflow-x-auto rounded border border-[var(--border)]">
                <table className="w-full min-w-[640px] text-left text-sm">
                  <thead className="bg-[var(--bg-elevated)] text-[var(--muted)]">
                    <tr>
                      <th className="px-3 py-2 font-medium">When</th>
                      <th className="px-3 py-2 font-medium">Type</th>
                      <th className="px-3 py-2 font-medium">Product</th>
                      <th className="px-3 py-2 font-medium">Qty</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.recent_movements.map((m) => (
                      <tr key={m.id} className="border-t border-[var(--border)]">
                        <td className="px-3 py-2 text-xs text-[var(--muted)]">
                          {new Date(m.created_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 capitalize">
                          {m.movement_type.replaceAll("_", " ")}
                        </td>
                        <td className="px-3 py-2">
                          <span className="font-mono text-xs">{m.sku}</span>{" "}
                          <span className="text-[var(--muted)]">{m.product_name}</span>
                        </td>
                        <td className="px-3 py-2 tabular-nums">{m.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}

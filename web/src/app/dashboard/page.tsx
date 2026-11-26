"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError, DashboardSummary } from "@/lib/api";

const SHORTCUTS = [
  { href: "/products", label: "Products", hint: "Create / list / search" },
  { href: "/purchase-orders", label: "Purchase orders", hint: "Receive against ordered POs" },
  { href: "/stock", label: "Stock", hint: "Balances + recent movements" },
  { href: "/transfers", label: "Transfers", hint: "Move stock between locations" },
  { href: "/counts", label: "Counts", hint: "Variance review + approval" },
  { href: "/reports", label: "Reports", hint: "Stock-on-hand + CSV export" },
  { href: "/reorder", label: "Reorder AI", hint: "Recommendations + draft PO" },
  { href: "/stockout-radar", label: "Stockout Radar", hint: "Transparent risk formula" },
  { href: "/ai-ask", label: "AI Q&A", hint: "Allowlisted read tools" },
] as const;

export default function DashboardPage() {
  return (
    <AuthGate>
      <DashboardView />
    </AuthGate>
  );
}

function DashboardView() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<DashboardSummary>("/dashboard/summary");
      setSummary(data);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const tiles = summary
    ? [
        { label: "Stock value", value: summary.stock_value, hint: "Qty × unit cost" },
        { label: "Low stock", value: String(summary.low_stock_items), hint: "At/below reorder point" },
        { label: "Out of stock", value: String(summary.out_of_stock_items), hint: "Qty ≤ 0" },
        {
          label: "Pending POs",
          value: String(summary.pending_purchase_orders),
          hint: "Draft / ordered / partial",
        },
        {
          label: "Recent movements",
          value: String(summary.recent_movement_count),
          hint: "Latest ledger rows",
        },
        {
          label: "Products",
          value: String(summary.product_count),
          hint: `${summary.location_count} locations`,
        },
      ]
    : [];

  return (
    <section className="max-w-5xl space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Overview</p>
          <h2 className="mt-2 text-3xl font-semibold">Dashboard</h2>
          <p className="mt-3 text-[var(--muted)] leading-relaxed">
            KPI tiles from seeded org data. Milestone 4 adds reports, CSV export, and a thin
            transfers / counts approval slice.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)]"
        >
          Refresh
        </button>
      </header>

      <StatusBanner error={error} />

      {loading ? (
        <p className="text-[var(--muted)]">Loading KPIs…</p>
      ) : !summary ? (
        <EmptyState title="No dashboard data" description="Sign in and ensure the API is seeded." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tiles.map((tile) => (
            <div
              key={tile.label}
              className="rounded border border-[var(--border)] bg-[var(--surface)]/50 px-4 py-4"
            >
              <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{tile.label}</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-[var(--accent)]">
                {tile.value}
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">{tile.hint}</p>
            </div>
          ))}
        </div>
      )}

      {summary ? (
        <p className="text-xs text-[var(--muted)]">
          Generated {new Date(summary.generated_at).toLocaleString()} · deterministic aggregation
          (not AI)
        </p>
      ) : null}

      <ul className="space-y-3 text-sm">
        {SHORTCUTS.map((item) => (
          <li
            key={item.href}
            className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3"
          >
            <Link href={item.href} className="text-[var(--accent)] hover:underline">
              {item.label}
            </Link>
            <span className="text-[var(--muted)]"> — {item.hint}</span>
          </li>
        ))}
        <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3 text-[var(--muted)]">
          Suppliers / Locations write / Settings — Coming Soon
        </li>
      </ul>
    </section>
  );
}

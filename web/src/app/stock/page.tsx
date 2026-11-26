"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import {
  apiFetch,
  ApiRequestError,
  Page,
  StockBalance,
  StockMovement,
} from "@/lib/api";

export default function StockPage() {
  return (
    <AuthGate>
      <StockView />
    </AuthGate>
  );
}

function StockView() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const balQs = new URLSearchParams({ page: "1", page_size: "40" });
      if (search.trim()) balQs.set("q", search.trim());
      const [balPage, movPage] = await Promise.all([
        apiFetch<Page<StockBalance>>(`/stock/balances?${balQs}`),
        apiFetch<Page<StockMovement>>("/stock/movements?page=1&page_size=30"),
      ]);
      setBalances(balPage.items);
      setMovements(movPage.items);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load stock");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="max-w-5xl space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Inventory</p>
        <h2 className="mt-2 text-3xl font-semibold">Stock</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          On-hand balances by location and recent immutable ledger movements.
        </p>
      </header>

      <form
        className="flex flex-col gap-2 sm:flex-row"
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          setSearch(q);
        }}
      >
        <input
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
          placeholder="Filter balances by SKU or name"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          type="submit"
          className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)]"
        >
          Filter
        </button>
      </form>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
      {loading ? <p className="text-[var(--muted)]">Loading stock…</p> : null}

      <div>
        <h3 className="mb-3 text-lg font-semibold">Balances</h3>
        {!loading && balances.length === 0 ? (
          <p className="text-[var(--muted)]">No balances found.</p>
        ) : (
          <div className="overflow-x-auto rounded border border-[var(--border)]">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="bg-[var(--bg-elevated)] text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2 font-medium">SKU</th>
                  <th className="px-3 py-2 font-medium">Product</th>
                  <th className="px-3 py-2 font-medium">Location</th>
                  <th className="px-3 py-2 font-medium">Qty</th>
                </tr>
              </thead>
              <tbody>
                {balances.map((b) => (
                  <tr key={b.id} className="border-t border-[var(--border)]">
                    <td className="px-3 py-2 font-mono text-xs">{b.product_sku}</td>
                    <td className="px-3 py-2">{b.product_name}</td>
                    <td className="px-3 py-2 text-[var(--muted)]">
                      {b.location_code} — {b.location_name}
                    </td>
                    <td className="px-3 py-2 font-medium">{b.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-3 text-lg font-semibold">Recent movements</h3>
        {!loading && movements.length === 0 ? (
          <p className="text-[var(--muted)]">No movements yet.</p>
        ) : (
          <div className="overflow-x-auto rounded border border-[var(--border)]">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-[var(--bg-elevated)] text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2 font-medium">When</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                  <th className="px-3 py-2 font-medium">Product</th>
                  <th className="px-3 py-2 font-medium">Qty</th>
                  <th className="px-3 py-2 font-medium">Balance after</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((m) => (
                  <tr key={m.id} className="border-t border-[var(--border)]">
                    <td className="px-3 py-2 text-xs text-[var(--muted)]">
                      {new Date(m.created_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 capitalize">{m.movement_type.replaceAll("_", " ")}</td>
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs">{m.product_sku}</span>{" "}
                      <span className="text-[var(--muted)]">{m.product_name}</span>
                    </td>
                    <td className="px-3 py-2">{m.quantity}</td>
                    <td className="px-3 py-2">{m.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

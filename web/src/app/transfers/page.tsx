"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import {
  apiFetch,
  ApiRequestError,
  Location,
  Page,
  Product,
  TransferDetail,
  TransferSummary,
} from "@/lib/api";

export default function TransfersPage() {
  return (
    <AuthGate>
      <TransfersView />
    </AuthGate>
  );
}

function TransfersView() {
  const [items, setItems] = useState<TransferSummary[]>([]);
  const [detail, setDetail] = useState<TransferDetail | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [receiving, setReceiving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    source_location_id: "",
    destination_location_id: "",
    product_id: "",
    quantity: "1",
    notes: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await apiFetch<Page<TransferSummary>>("/stock/transfers");
      setItems(page.items);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load transfers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    void (async () => {
      try {
        const [locs, prodPage] = await Promise.all([
          apiFetch<Location[]>("/locations"),
          apiFetch<Page<Product>>("/products?page=1&page_size=50"),
        ]);
        setLocations(locs);
        setProducts(prodPage.items);
        setForm((f) => ({
          ...f,
          source_location_id: f.source_location_id || locs[0]?.id || "",
          destination_location_id: f.destination_location_id || locs[1]?.id || locs[0]?.id || "",
          product_id: f.product_id || prodPage.items[0]?.id || "",
        }));
      } catch {
        /* form shows validation when opened */
      }
    })();
  }, []);

  async function openTransfer(id: string) {
    setError(null);
    try {
      const t = await apiFetch<TransferDetail>(`/stock/transfers/${id}`);
      setDetail(t);
    } catch (e) {
      setDetail(null);
      setError(e instanceof ApiRequestError ? e.message : "Failed to load transfer");
    }
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (form.source_location_id === form.destination_location_id) {
      setError("Source and destination must differ");
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await apiFetch<TransferDetail>("/stock/transfers", {
        method: "POST",
        body: JSON.stringify({
          source_location_id: form.source_location_id,
          destination_location_id: form.destination_location_id,
          lines: [{ product_id: form.product_id, quantity: form.quantity }],
          notes: form.notes.trim() || null,
          mark_in_transit: true,
        }),
      });
      setShowForm(false);
      setSuccess(`Transfer created (${created.status}). Receive to move stock.`);
      await load();
      await openTransfer(created.id);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  async function onReceive() {
    if (!detail) return;
    const ok = window.confirm(
      "Receive this transfer? Stock will move from source to destination (total qty preserved).",
    );
    if (!ok) return;
    setReceiving(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await apiFetch<{ status: string; preserved_total: boolean }>(
        `/stock/transfers/${detail.id}/receive`,
        { method: "POST" },
      );
      setSuccess(
        `Transfer ${result.status}. Total preserved: ${result.preserved_total ? "yes" : "no"}.`,
      );
      await openTransfer(detail.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Receive failed");
    } finally {
      setReceiving(false);
    }
  }

  const receivable = detail && (detail.status === "initiated" || detail.status === "in_transit");

  return (
    <section className="max-w-5xl space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Operations</p>
          <h2 className="mt-2 text-3xl font-semibold">Stock transfers</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Thin slice: create in-transit transfer, then receive to move balances. Total quantity is
            preserved across locations.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)]"
        >
          {showForm ? "Close form" : "New transfer"}
        </button>
      </header>

      <StatusBanner error={error} success={success} />

      {showForm ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm">
            <span className="text-[var(--muted)]">Source</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.source_location_id}
              onChange={(e) => setForm({ ...form, source_location_id: e.target.value })}
            >
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.code} — {l.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Destination</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.destination_location_id}
              onChange={(e) => setForm({ ...form, destination_location_id: e.target.value })}
            >
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.code} — {l.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Product</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.product_id}
              onChange={(e) => setForm({ ...form, product_id: e.target.value })}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.sku} — {p.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Quantity</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Notes</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-60"
            >
              {saving ? "Creating…" : "Create transfer"}
            </button>
          </div>
        </form>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm uppercase tracking-wide text-[var(--muted)]">Transfers</h3>
          {loading ? (
            <p className="text-[var(--muted)]">Loading…</p>
          ) : items.length === 0 ? (
            <EmptyState title="No transfers yet" description="Create one to move stock." />
          ) : (
            <ul className="space-y-2">
              {items.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => void openTransfer(t.id)}
                    className={`w-full rounded border px-3 py-3 text-left text-sm ${
                      detail?.id === t.id
                        ? "border-[var(--accent)] bg-[var(--surface)]"
                        : "border-[var(--border)] bg-[var(--bg-elevated)]/60 hover:border-[var(--accent-dim)]"
                    }`}
                  >
                    <div className="flex justify-between gap-2">
                      <span className="font-mono text-xs">{t.id.slice(0, 8)}…</span>
                      <span className="text-xs capitalize text-[var(--muted)]">
                        {t.status.replaceAll("_", " ")}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {t.source_location_code} → {t.destination_location_code} · {t.line_count}{" "}
                      lines
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          {!detail ? (
            <EmptyState title="Select a transfer" description="View lines and receive when ready." />
          ) : (
            <div className="space-y-4 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4">
              <div>
                <h3 className="text-lg font-semibold capitalize">
                  {detail.status.replaceAll("_", " ")}
                </h3>
                <p className="text-sm text-[var(--muted)]">
                  {detail.source_location_code} → {detail.destination_location_code}
                </p>
              </div>
              <ul className="space-y-2 text-sm">
                {detail.lines.map((ln) => (
                  <li key={ln.id} className="border-t border-[var(--border)] pt-2">
                    {ln.product_sku} — {ln.product_name}:{" "}
                    <span className="font-medium">{ln.quantity}</span>
                  </li>
                ))}
              </ul>
              {receivable ? (
                <button
                  type="button"
                  disabled={receiving}
                  onClick={() => void onReceive()}
                  className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-60"
                >
                  {receiving ? "Receiving…" : "Receive transfer"}
                </button>
              ) : (
                <p className="text-sm text-[var(--warn)]">
                  Not receivable (status: {detail.status}).
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

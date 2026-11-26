"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import {
  apiFetch,
  ApiRequestError,
  Page,
  PurchaseOrderDetail,
  PurchaseOrderSummary,
} from "@/lib/api";

export default function PurchaseOrdersPage() {
  return (
    <AuthGate>
      <PurchaseOrdersView />
    </AuthGate>
  );
}

function PurchaseOrdersView() {
  const [items, setItems] = useState<PurchaseOrderSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PurchaseOrderDetail | null>(null);
  const [qtyMap, setQtyMap] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [receiving, setReceiving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await apiFetch<Page<PurchaseOrderSummary>>(
        "/purchase-orders?page=1&page_size=50",
      );
      setItems(page.items);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load POs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  async function openPo(id: string) {
    setSelectedId(id);
    setMessage(null);
    setError(null);
    setNotes("");
    try {
      const po = await apiFetch<PurchaseOrderDetail>(`/purchase-orders/${id}`);
      setDetail(po);
      const initial: Record<string, string> = {};
      for (const line of po.lines) {
        const rem = Number(line.quantity_remaining);
        initial[line.id] = rem > 0 ? String(rem) : "0";
      }
      setQtyMap(initial);
    } catch (e) {
      setDetail(null);
      setError(e instanceof ApiRequestError ? e.message : "Failed to load PO");
    }
  }

  async function onReceive(e: FormEvent) {
    e.preventDefault();
    if (!detail) return;
    setReceiving(true);
    setError(null);
    setMessage(null);
    try {
      const lines = detail.lines
        .map((line) => ({
          purchase_order_line_id: line.id,
          quantity: qtyMap[line.id] ?? "0",
        }))
        .filter((l) => Number(l.quantity) > 0);

      if (lines.length === 0) {
        setError("Enter at least one quantity to receive");
        return;
      }

      const result = await apiFetch<{ status: string; po_number: string }>("/receipts", {
        method: "POST",
        body: JSON.stringify({
          purchase_order_id: detail.id,
          lines,
          discrepancy_notes: notes.trim() || null,
        }),
      });
      setMessage(`Received against ${result.po_number}. New status: ${result.status}.`);
      await openPo(detail.id);
      await loadList();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Receive failed");
    } finally {
      setReceiving(false);
    }
  }

  const receivable =
    detail && (detail.status === "ordered" || detail.status === "partially_received");

  return (
    <section className="max-w-5xl space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Purchasing</p>
        <h2 className="mt-2 text-3xl font-semibold">Purchase orders</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Open an ordered / partially received PO and receive lines. Stock balance and ledger update
          atomically.
        </p>
      </header>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
      {message ? <p className="text-sm text-[var(--accent)]">{message}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm uppercase tracking-wide text-[var(--muted)]">Orders</h3>
          {loading ? (
            <p className="text-[var(--muted)]">Loading…</p>
          ) : (
            <ul className="space-y-2">
              {items.map((po) => (
                <li key={po.id}>
                  <button
                    type="button"
                    onClick={() => void openPo(po.id)}
                    className={`w-full rounded border px-3 py-3 text-left text-sm ${
                      selectedId === po.id
                        ? "border-[var(--accent)] bg-[var(--surface)]"
                        : "border-[var(--border)] bg-[var(--bg-elevated)]/60 hover:border-[var(--accent-dim)]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{po.po_number}</span>
                      <span className="text-xs capitalize text-[var(--muted)]">
                        {po.status.replaceAll("_", " ")}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {po.supplier_name ?? "Supplier"} · {po.location_name ?? "Location"} ·{" "}
                      {po.line_count} lines
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          {!detail ? (
            <p className="text-[var(--muted)]">Select a purchase order to view lines and receive.</p>
          ) : (
            <div className="space-y-4 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4">
              <div>
                <h3 className="text-xl font-semibold">{detail.po_number}</h3>
                <p className="text-sm text-[var(--muted)]">
                  {detail.supplier_name} → {detail.location_name} ·{" "}
                  <span className="capitalize">{detail.status.replaceAll("_", " ")}</span>
                </p>
              </div>

              <form onSubmit={onReceive} className="space-y-3">
                {detail.lines.map((line) => (
                  <div
                    key={line.id}
                    className="grid gap-2 border-t border-[var(--border)] pt-3 sm:grid-cols-[1fr_auto]"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {line.product_sku} — {line.product_name}
                      </p>
                      <p className="text-xs text-[var(--muted)]">
                        Ordered {line.quantity_ordered} · Received {line.quantity_received} ·
                        Remaining {line.quantity_remaining}
                      </p>
                    </div>
                    <label className="text-sm">
                      <span className="text-[var(--muted)]">Receive qty</span>
                      <input
                        className="mt-1 w-28 rounded border border-[var(--border)] bg-[var(--surface)] px-2 py-1.5"
                        value={qtyMap[line.id] ?? "0"}
                        disabled={!receivable}
                        onChange={(e) =>
                          setQtyMap((m) => ({ ...m, [line.id]: e.target.value }))
                        }
                      />
                    </label>
                  </div>
                ))}

                <label className="block text-sm">
                  <span className="text-[var(--muted)]">Discrepancy notes (optional)</span>
                  <textarea
                    className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
                    rows={2}
                    value={notes}
                    disabled={!receivable}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </label>

                {receivable ? (
                  <button
                    type="submit"
                    disabled={receiving}
                    className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60"
                  >
                    {receiving ? "Receiving…" : "Receive stock"}
                  </button>
                ) : (
                  <p className="text-sm text-[var(--warn)]">
                    This PO is not receivable (status: {detail.status}).
                  </p>
                )}
              </form>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

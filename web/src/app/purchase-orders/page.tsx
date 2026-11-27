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
  PurchaseOrderDetail,
  PurchaseOrderSummary,
  Supplier,
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
  const [acting, setActing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [createForm, setCreateForm] = useState({
    supplier_id: "",
    location_id: "",
    product_id: "",
    quantity: "10",
    notes: "",
  });

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

  useEffect(() => {
    void (async () => {
      try {
        const [s, loc, prod] = await Promise.all([
          apiFetch<Supplier[]>("/suppliers"),
          apiFetch<Location[]>("/locations"),
          apiFetch<Page<Product>>("/products?page=1&page_size=50"),
        ]);
        setSuppliers(s);
        setLocations(loc);
        setProducts(prod.items);
        setCreateForm((f) => ({
          ...f,
          supplier_id: f.supplier_id || s[0]?.id || "",
          location_id: f.location_id || loc[0]?.id || "",
          product_id: f.product_id || prod.items[0]?.id || "",
        }));
      } catch {
        /* create form will surface errors on submit */
      }
    })();
  }, []);

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

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setActing(true);
    setError(null);
    setMessage(null);
    try {
      const po = await apiFetch<PurchaseOrderDetail>("/purchase-orders", {
        method: "POST",
        body: JSON.stringify({
          supplier_id: createForm.supplier_id,
          location_id: createForm.location_id,
          notes: createForm.notes || null,
          lines: [
            {
              product_id: createForm.product_id,
              quantity_ordered: createForm.quantity,
            },
          ],
        }),
      });
      setShowCreate(false);
      setMessage(`Draft ${po.po_number} created.`);
      await loadList();
      await openPo(po.id);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Create failed");
    } finally {
      setActing(false);
    }
  }

  async function onSubmitPo() {
    if (!detail) return;
    const ok = window.confirm(`Submit ${detail.po_number}? Status becomes ordered (receivable).`);
    if (!ok) return;
    setActing(true);
    setError(null);
    try {
      const po = await apiFetch<PurchaseOrderDetail>(`/purchase-orders/${detail.id}/submit`, {
        method: "POST",
      });
      setMessage(`Submitted ${po.po_number}.`);
      setDetail(po);
      await loadList();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Submit failed");
    } finally {
      setActing(false);
    }
  }

  async function onCancelPo() {
    if (!detail) return;
    const ok = window.confirm(`Cancel ${detail.po_number}?`);
    if (!ok) return;
    setActing(true);
    setError(null);
    try {
      const po = await apiFetch<PurchaseOrderDetail>(`/purchase-orders/${detail.id}/cancel`, {
        method: "POST",
      });
      setMessage(`Cancelled ${po.po_number}.`);
      setDetail(po);
      await loadList();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Cancel failed");
    } finally {
      setActing(false);
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

      const ok = window.confirm(
        `Receive ${lines.length} line(s) against ${detail.po_number}? Stock balance and ledger will update.`,
      );
      if (!ok) return;

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
  const isDraft = detail?.status === "draft";
  const cancellable = detail && (detail.status === "draft" || detail.status === "ordered");

  return (
    <section className="max-w-5xl space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Purchasing</p>
          <h2 className="mt-2 text-3xl font-semibold">Purchase orders</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Create draft → submit (ordered) → receive. Cancel draft/ordered before receive.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)]"
        >
          {showCreate ? "Close form" : "New draft PO"}
        </button>
      </header>

      <StatusBanner error={error} success={message} />

      {showCreate ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm">
            <span className="text-[var(--muted)]">Supplier</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={createForm.supplier_id}
              onChange={(e) => setCreateForm({ ...createForm, supplier_id: e.target.value })}
            >
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Receive location</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={createForm.location_id}
              onChange={(e) => setCreateForm({ ...createForm, location_id: e.target.value })}
            >
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.code} — {l.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Product</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={createForm.product_id}
              onChange={(e) => setCreateForm({ ...createForm, product_id: e.target.value })}
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
              value={createForm.quantity}
              onChange={(e) => setCreateForm({ ...createForm, quantity: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Notes</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={createForm.notes}
              onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
            />
          </label>
          <button
            type="submit"
            disabled={acting}
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60 sm:col-span-2 sm:w-fit"
          >
            {acting ? "Creating…" : "Create draft"}
          </button>
        </form>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm uppercase tracking-wide text-[var(--muted)]">Orders</h3>
          {loading ? (
            <p className="text-[var(--muted)]">Loading…</p>
          ) : items.length === 0 ? (
            <EmptyState
              title="No purchase orders"
              description="Create a draft PO or confirm an AI draft."
            />
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

              <div className="flex flex-wrap gap-2">
                {isDraft ? (
                  <button
                    type="button"
                    disabled={acting}
                    onClick={() => void onSubmitPo()}
                    className="rounded bg-[var(--accent-dim)] px-3 py-1.5 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-60"
                  >
                    Submit
                  </button>
                ) : null}
                {cancellable ? (
                  <button
                    type="button"
                    disabled={acting}
                    onClick={() => void onCancelPo()}
                    className="rounded border border-[var(--danger)] px-3 py-1.5 text-sm text-[var(--danger)] hover:bg-[var(--surface)] disabled:opacity-60"
                  >
                    Cancel PO
                  </button>
                ) : null}
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
                    {isDraft
                      ? "Submit this draft before receiving."
                      : `This PO is not receivable (status: ${detail.status}).`}
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

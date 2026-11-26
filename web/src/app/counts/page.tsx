"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import {
  apiFetch,
  ApiRequestError,
  CountDetail,
  CountSummary,
  Location,
  Page,
  Product,
} from "@/lib/api";

export default function CountsPage() {
  return (
    <AuthGate>
      <CountsView />
    </AuthGate>
  );
}

function CountsView() {
  const [items, setItems] = useState<CountSummary[]>([]);
  const [detail, setDetail] = useState<CountDetail | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [approvalReason, setApprovalReason] = useState("");
  const [form, setForm] = useState({
    location_id: "",
    product_id: "",
    counted_quantity: "0",
    notes: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await apiFetch<Page<CountSummary>>("/stock/counts");
      setItems(page.items);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load counts");
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
          location_id: f.location_id || locs[0]?.id || "",
          product_id: f.product_id || prodPage.items[0]?.id || "",
        }));
      } catch {
        /* ignore */
      }
    })();
  }, []);

  async function openCount(id: string) {
    setError(null);
    try {
      const c = await apiFetch<CountDetail>(`/stock/counts/${id}`);
      setDetail(c);
      setApprovalReason("");
    } catch (e) {
      setDetail(null);
      setError(e instanceof ApiRequestError ? e.message : "Failed to load count");
    }
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await apiFetch<CountDetail>("/stock/counts", {
        method: "POST",
        body: JSON.stringify({
          location_id: form.location_id,
          submit: true,
          notes: form.notes.trim() || null,
          lines: [
            {
              product_id: form.product_id,
              counted_quantity: form.counted_quantity,
            },
          ],
        }),
      });
      setShowForm(false);
      setSuccess("Count submitted for approval.");
      await load();
      await openCount(created.id);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  async function onApprove() {
    if (!detail) return;
    const hasVariance = detail.lines.some((ln) => Number(ln.variance) !== 0);
    if (hasVariance && !approvalReason.trim()) {
      setError("Enter an approval reason for non-zero variance.");
      return;
    }
    const ok = window.confirm(
      "Approve this count? Variances will adjust stock balances and write ledger movements.",
    );
    if (!ok) return;
    setApproving(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await apiFetch<{ status: string; adjustments_applied: number }>(
        `/stock/counts/${detail.id}/approve`,
        {
          method: "POST",
          body: JSON.stringify({
            approval_reason: approvalReason.trim() || null,
          }),
        },
      );
      setSuccess(
        `Count ${result.status}. Adjustments applied: ${result.adjustments_applied}.`,
      );
      await openCount(detail.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  }

  return (
    <section className="max-w-5xl space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Operations</p>
          <h2 className="mt-2 text-3xl font-semibold">Stock counts</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Thin approval slice: submit counted qty, review variance, approve with a mandatory
            reason when variance ≠ 0.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)]"
        >
          {showForm ? "Close form" : "New count"}
        </button>
      </header>

      <StatusBanner error={error} success={success} />

      {showForm ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm">
            <span className="text-[var(--muted)]">Location</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.location_id}
              onChange={(e) => setForm({ ...form, location_id: e.target.value })}
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
            <span className="text-[var(--muted)]">Counted quantity</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.counted_quantity}
              onChange={(e) => setForm({ ...form, counted_quantity: e.target.value })}
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
              {saving ? "Submitting…" : "Submit count"}
            </button>
          </div>
        </form>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm uppercase tracking-wide text-[var(--muted)]">Sessions</h3>
          {loading ? (
            <p className="text-[var(--muted)]">Loading…</p>
          ) : items.length === 0 ? (
            <EmptyState title="No counts yet" description="Submit a counted quantity to start." />
          ) : (
            <ul className="space-y-2">
              {items.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => void openCount(c.id)}
                    className={`w-full rounded border px-3 py-3 text-left text-sm ${
                      detail?.id === c.id
                        ? "border-[var(--accent)] bg-[var(--surface)]"
                        : "border-[var(--border)] bg-[var(--bg-elevated)]/60 hover:border-[var(--accent-dim)]"
                    }`}
                  >
                    <div className="flex justify-between gap-2">
                      <span>{c.location_code ?? "Location"}</span>
                      <span className="text-xs capitalize text-[var(--muted)]">{c.status}</span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {c.line_count} lines · {new Date(c.created_at).toLocaleString()}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          {!detail ? (
            <EmptyState title="Select a count" description="Review variance before approval." />
          ) : (
            <div className="space-y-4 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4">
              <div>
                <h3 className="text-lg font-semibold capitalize">{detail.status}</h3>
                <p className="text-sm text-[var(--muted)]">
                  {detail.location_code} — {detail.location_name}
                </p>
              </div>
              <ul className="space-y-3 text-sm">
                {detail.lines.map((ln) => (
                  <li key={ln.id} className="border-t border-[var(--border)] pt-3">
                    <p className="font-medium">
                      {ln.product_sku} — {ln.product_name}
                    </p>
                    <p className="text-xs text-[var(--muted)]">
                      Expected {ln.expected_quantity} · Counted {ln.counted_quantity} · Variance{" "}
                      <span className={Number(ln.variance) !== 0 ? "text-[var(--warn)]" : ""}>
                        {ln.variance}
                      </span>
                    </p>
                  </li>
                ))}
              </ul>
              {detail.status === "submitted" ? (
                <div className="space-y-3">
                  <label className="block text-sm">
                    <span className="text-[var(--muted)]">
                      Approval reason (required if variance ≠ 0)
                    </span>
                    <textarea
                      className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
                      rows={2}
                      value={approvalReason}
                      onChange={(e) => setApprovalReason(e.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    disabled={approving}
                    onClick={() => void onApprove()}
                    className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm text-white hover:bg-[var(--accent)] disabled:opacity-60"
                  >
                    {approving ? "Approving…" : "Approve count"}
                  </button>
                </div>
              ) : (
                <p className="text-sm text-[var(--muted)]">
                  Status: {detail.status}
                  {detail.approved_at
                    ? ` · approved ${new Date(detail.approved_at).toLocaleString()}`
                    : ""}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

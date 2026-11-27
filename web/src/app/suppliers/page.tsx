"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError } from "@/lib/api";

type Supplier = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  lead_time_days: number;
  notes: string | null;
  is_active: boolean;
};

export default function SuppliersPage() {
  return (
    <AuthGate>
      <SuppliersView />
    </AuthGate>
  );
}

function SuppliersView() {
  const [items, setItems] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    lead_time_days: "7",
    notes: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await apiFetch<Supplier[]>("/suppliers?active_only=true");
      setItems(rows);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load suppliers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await apiFetch<Supplier>("/suppliers", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          email: form.email || null,
          phone: form.phone || null,
          lead_time_days: Number(form.lead_time_days) || 7,
          notes: form.notes || null,
          is_active: true,
        }),
      });
      setShowForm(false);
      setForm({ name: "", email: "", phone: "", lead_time_days: "7", notes: "" });
      setMessage("Supplier created.");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="max-w-5xl space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Purchasing</p>
          <h2 className="mt-2 text-3xl font-semibold">Suppliers</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Directory for POs and lead-time inputs to Stockout Radar.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)]"
        >
          {showForm ? "Close form" : "New supplier"}
        </button>
      </header>

      <StatusBanner error={error} success={message} />

      {showForm ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Name</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Email</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Phone</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Lead time (days)</span>
            <input
              required
              type="number"
              min={0}
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.lead_time_days}
              onChange={(e) => setForm({ ...form, lead_time_days: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Notes</span>
            <textarea
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              rows={2}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </label>
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60 sm:col-span-2 sm:w-fit"
          >
            {saving ? "Saving…" : "Create supplier"}
          </button>
        </form>
      ) : null}

      {loading ? (
        <p className="text-[var(--muted)]">Loading…</p>
      ) : items.length === 0 ? (
        <EmptyState title="No suppliers" description="Create a supplier to start purchasing." />
      ) : (
        <ul className="space-y-2">
          {items.map((s) => (
            <li
              key={s.id}
              className="rounded border border-[var(--border)] bg-[var(--bg-elevated)]/60 px-4 py-3"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-medium">{s.name}</p>
                <p className="text-xs text-[var(--muted)]">Lead {s.lead_time_days}d</p>
              </div>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {[s.email, s.phone].filter(Boolean).join(" · ") || "No contact"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

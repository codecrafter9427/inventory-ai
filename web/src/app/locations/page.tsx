"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError, Location } from "@/lib/api";

export default function LocationsPage() {
  return (
    <AuthGate>
      <LocationsView />
    </AuthGate>
  );
}

function LocationsView() {
  const [items, setItems] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name: "",
    address: "",
    bin_shelf_notes: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await apiFetch<Location[]>("/locations");
      setItems(rows);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load locations");
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
      await apiFetch("/locations", {
        method: "POST",
        body: JSON.stringify({
          code: form.code,
          name: form.name,
          address: form.address || null,
          bin_shelf_notes: form.bin_shelf_notes || null,
          is_active: true,
        }),
      });
      setShowForm(false);
      setForm({ code: "", name: "", address: "", bin_shelf_notes: "" });
      setMessage("Location created.");
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
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Warehouse</p>
          <h2 className="mt-2 text-3xl font-semibold">Locations</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Warehouses and bins used for receiving, transfers, and balances.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)]"
        >
          {showForm ? "Close form" : "New location"}
        </button>
      </header>

      <StatusBanner error={error} success={message} />

      {showForm ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm">
            <span className="text-[var(--muted)]">Code</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Name</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Address</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="text-[var(--muted)]">Bin / shelf notes</span>
            <textarea
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              rows={2}
              value={form.bin_shelf_notes}
              onChange={(e) => setForm({ ...form, bin_shelf_notes: e.target.value })}
            />
          </label>
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60 sm:col-span-2 sm:w-fit"
          >
            {saving ? "Saving…" : "Create location"}
          </button>
        </form>
      ) : null}

      {loading ? (
        <p className="text-[var(--muted)]">Loading…</p>
      ) : items.length === 0 ? (
        <EmptyState title="No locations" description="Create a warehouse or bay to hold stock." />
      ) : (
        <ul className="space-y-2">
          {items.map((loc) => (
            <li
              key={loc.id}
              className="rounded border border-[var(--border)] bg-[var(--bg-elevated)]/60 px-4 py-3"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-medium">
                  <span className="text-[var(--accent)]">{loc.code}</span> — {loc.name}
                </p>
              </div>
              {loc.address || loc.bin_shelf_notes ? (
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {[loc.address, loc.bin_shelf_notes].filter(Boolean).join(" · ")}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

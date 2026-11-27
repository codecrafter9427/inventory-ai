"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { StatusBanner } from "@/components/StatusBanner";
import { apiFetch, ApiRequestError } from "@/lib/api";

type OrgSettings = {
  id: string;
  name: string;
  slug: string;
  default_reorder_point: string;
  default_safety_stock: string;
  default_lead_time_days: number;
};

type Role = { id: string; code: string; name: string; description: string | null };
type UnitRow = { id: string; code: string; name: string };

export default function SettingsPage() {
  return (
    <AuthGate>
      <SettingsView />
    </AuthGate>
  );
}

function SettingsView() {
  const [org, setOrg] = useState<OrgSettings | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [units, setUnits] = useState<UnitRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [unitForm, setUnitForm] = useState({ code: "", name: "" });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [o, r, u] = await Promise.all([
        apiFetch<OrgSettings>("/settings/organization"),
        apiFetch<Role[]>("/settings/roles"),
        apiFetch<UnitRow[]>("/settings/units"),
      ]);
      setOrg(o);
      setRoles(r);
      setUnits(u);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load settings");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSaveOrg(e: FormEvent) {
    e.preventDefault();
    if (!org) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await apiFetch<OrgSettings>("/settings/organization", {
        method: "PATCH",
        body: JSON.stringify({
          name: org.name,
          default_reorder_point: org.default_reorder_point,
          default_safety_stock: org.default_safety_stock,
          default_lead_time_days: Number(org.default_lead_time_days),
        }),
      });
      setOrg(updated);
      setMessage("Organization settings saved (owner only).");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function onCreateUnit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await apiFetch("/settings/units", {
        method: "POST",
        body: JSON.stringify(unitForm),
      });
      setUnitForm({ code: "", name: "" });
      setMessage("Unit created.");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Unit create failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="max-w-3xl space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Organization</p>
        <h2 className="mt-2 text-3xl font-semibold">Settings</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Org profile, roles (read-only), units, and reorder defaults. Password / JWT notes live in
          README.
        </p>
      </header>

      <StatusBanner error={error} success={message} />

      {org ? (
        <form
          onSubmit={onSaveOrg}
          className="space-y-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4"
        >
          <h3 className="text-lg font-semibold">Organization</h3>
          <p className="text-xs text-[var(--muted)]">Slug: {org.slug}</p>
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Name</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={org.name}
              onChange={(e) => setOrg({ ...org, name: e.target.value })}
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="text-sm">
              <span className="text-[var(--muted)]">Default reorder point</span>
              <input
                className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
                value={org.default_reorder_point}
                onChange={(e) => setOrg({ ...org, default_reorder_point: e.target.value })}
              />
            </label>
            <label className="text-sm">
              <span className="text-[var(--muted)]">Default safety stock</span>
              <input
                className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
                value={org.default_safety_stock}
                onChange={(e) => setOrg({ ...org, default_safety_stock: e.target.value })}
              />
            </label>
            <label className="text-sm">
              <span className="text-[var(--muted)]">Default lead time (days)</span>
              <input
                type="number"
                min={0}
                className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
                value={org.default_lead_time_days}
                onChange={(e) =>
                  setOrg({ ...org, default_lead_time_days: Number(e.target.value) || 0 })
                }
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save org settings"}
          </button>
        </form>
      ) : (
        <p className="text-[var(--muted)]">Loading organization…</p>
      )}

      <div className="space-y-2 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4">
        <h3 className="text-lg font-semibold">Roles</h3>
        <p className="text-xs text-[var(--muted)]">Read-only directory for this organization.</p>
        <ul className="mt-2 space-y-2">
          {roles.map((r) => (
            <li key={r.id} className="text-sm">
              <span className="font-medium capitalize">{r.name}</span>{" "}
              <span className="text-[var(--muted)]">({r.code})</span>
              {r.description ? (
                <span className="block text-xs text-[var(--muted)]">{r.description}</span>
              ) : null}
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4">
        <h3 className="text-lg font-semibold">Units</h3>
        <ul className="space-y-1 text-sm">
          {units.map((u) => (
            <li key={u.id}>
              <span className="font-medium">{u.code}</span> — {u.name}
            </li>
          ))}
        </ul>
        <form onSubmit={onCreateUnit} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
          <input
            required
            placeholder="Code"
            className="rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
            value={unitForm.code}
            onChange={(e) => setUnitForm({ ...unitForm, code: e.target.value })}
          />
          <input
            required
            placeholder="Name"
            className="rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
            value={unitForm.name}
            onChange={(e) => setUnitForm({ ...unitForm, name: e.target.value })}
          />
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60"
          >
            Add unit
          </button>
        </form>
      </div>
    </section>
  );
}

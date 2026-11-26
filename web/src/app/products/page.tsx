"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { EmptyState } from "@/components/EmptyState";
import { StatusBanner } from "@/components/StatusBanner";
import {
  apiFetch,
  ApiRequestError,
  Category,
  Page,
  Product,
  Unit,
} from "@/lib/api";

export default function ProductsPage() {
  return (
    <AuthGate>
      <ProductsView />
    </AuthGate>
  );
}

function ProductsView() {
  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    sku: "",
    name: "",
    barcode: "",
    unit_id: "",
    category_id: "",
    cost: "0",
    selling_price: "0",
    reorder_point: "0",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ page: "1", page_size: "50" });
      if (search.trim()) qs.set("q", search.trim());
      const page = await apiFetch<Page<Product>>(`/products?${qs}`);
      setItems(page.items);
      setTotal(page.total);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    void (async () => {
      try {
        const [u, c] = await Promise.all([
          apiFetch<Unit[]>("/units"),
          apiFetch<Category[]>("/categories"),
        ]);
        setUnits(u);
        setCategories(c);
        if (u[0]) setForm((f) => ({ ...f, unit_id: f.unit_id || u[0].id }));
      } catch {
        /* ignore bootstrap errors; create form will show validation */
      }
    })();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiFetch<Product>("/products", {
        method: "POST",
        body: JSON.stringify({
          sku: form.sku,
          name: form.name,
          barcode: form.barcode || null,
          unit_id: form.unit_id,
          category_id: form.category_id || null,
          cost: form.cost,
          selling_price: form.selling_price,
          reorder_point: form.reorder_point,
          is_active: true,
        }),
      });
      setShowForm(false);
      setForm((f) => ({
        ...f,
        sku: "",
        name: "",
        barcode: "",
        cost: "0",
        selling_price: "0",
        reorder_point: "0",
      }));
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
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Catalog</p>
          <h2 className="mt-2 text-3xl font-semibold">Products</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Create and search by SKU, name, or barcode. {total} in catalog.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)]"
        >
          {showForm ? "Close form" : "New product"}
        </button>
      </header>

      {showForm ? (
        <form
          onSubmit={onCreate}
          className="grid gap-3 rounded border border-[var(--border)] bg-[var(--bg-elevated)]/70 p-4 sm:grid-cols-2"
        >
          <label className="text-sm">
            <span className="text-[var(--muted)]">SKU</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
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
          <label className="text-sm">
            <span className="text-[var(--muted)]">Barcode</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.barcode}
              onChange={(e) => setForm({ ...form, barcode: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Unit</span>
            <select
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.unit_id}
              onChange={(e) => setForm({ ...form, unit_id: e.target.value })}
            >
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.code} — {u.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Category</span>
            <select
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            >
              <option value="">— none —</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Cost</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.cost}
              onChange={(e) => setForm({ ...form, cost: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Selling price</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.selling_price}
              onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="text-[var(--muted)]">Reorder point</span>
            <input
              required
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
              value={form.reorder_point}
              onChange={(e) => setForm({ ...form, reorder_point: e.target.value })}
            />
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-[var(--accent-dim)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60"
            >
              {saving ? "Saving…" : "Create product"}
            </button>
          </div>
        </form>
      ) : null}

      <form
        className="flex flex-col gap-2 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(q);
        }}
      >
        <input
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
          placeholder="Search SKU, name, or barcode"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          type="submit"
          className="rounded border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-2 text-sm hover:border-[var(--accent)]"
        >
          Search
        </button>
      </form>

      <StatusBanner error={error} />

      {loading ? (
        <p className="text-[var(--muted)]">Loading products…</p>
      ) : items.length === 0 ? (
        <EmptyState
          title="No products match"
          description="Try another search or create a product."
        />
      ) : (
        <div className="overflow-x-auto rounded border border-[var(--border)]">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-[var(--bg-elevated)] text-[var(--muted)]">
              <tr>
                <th className="px-3 py-2 font-medium">SKU</th>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Barcode</th>
                <th className="px-3 py-2 font-medium">Unit</th>
                <th className="px-3 py-2 font-medium">Price</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id} className="border-t border-[var(--border)]">
                  <td className="px-3 py-2 font-mono text-xs">{p.sku}</td>
                  <td className="px-3 py-2">{p.name}</td>
                  <td className="px-3 py-2 font-mono text-xs text-[var(--muted)]">
                    {p.barcode ?? "—"}
                  </td>
                  <td className="px-3 py-2">{p.unit_code ?? "—"}</td>
                  <td className="px-3 py-2">{p.selling_price}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

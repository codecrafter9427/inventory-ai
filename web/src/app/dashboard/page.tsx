"use client";

import Link from "next/link";
import { AuthGate } from "@/components/AuthGate";

export default function DashboardPage() {
  return (
    <AuthGate>
      <section className="max-w-2xl">
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Overview</p>
        <h2 className="mt-2 text-3xl font-semibold">Dashboard</h2>
        <p className="mt-3 text-[var(--muted)] leading-relaxed">
          Milestone 2 vertical slice is live: create/search products, receive purchase orders
          (atomic balance + ledger), and inspect stock. KPI tiles remain Coming Soon.
        </p>
        <ul className="mt-8 space-y-3 text-sm">
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/products" className="text-[var(--accent)] hover:underline">
              Products
            </Link>
            <span className="text-[var(--muted)]"> — create / list / search</span>
          </li>
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/purchase-orders" className="text-[var(--accent)] hover:underline">
              Purchase orders
            </Link>
            <span className="text-[var(--muted)]"> — receive against ordered POs</span>
          </li>
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/stock" className="text-[var(--accent)] hover:underline">
              Stock
            </Link>
            <span className="text-[var(--muted)]"> — balances + recent movements</span>
          </li>
          {[
            "Stock value metrics — Coming Soon",
            "Low / out-of-stock alerts — Coming Soon",
            "Stockout Radar — Coming Soon",
          ].map((item) => (
            <li
              key={item}
              className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3 text-[var(--muted)]"
            >
              {item}
            </li>
          ))}
        </ul>
      </section>
    </AuthGate>
  );
}

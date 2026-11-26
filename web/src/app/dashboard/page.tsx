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
          Milestone 3 adds reorder recommendations, Stockout Radar, and inventory Q&amp;A (DemoAI
          offline; Ollama optional). Catalog + receive from M2 remain available.
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
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/reorder" className="text-[var(--accent)] hover:underline">
              Reorder AI
            </Link>
            <span className="text-[var(--muted)]"> — recommendations + confirm draft PO</span>
          </li>
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/stockout-radar" className="text-[var(--accent)] hover:underline">
              Stockout Radar
            </Link>
            <span className="text-[var(--muted)]"> — transparent risk formula</span>
          </li>
          <li className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-4 py-3">
            <Link href="/ai-ask" className="text-[var(--accent)] hover:underline">
              AI Q&amp;A
            </Link>
            <span className="text-[var(--muted)]"> — allowlisted read tools</span>
          </li>
          {["Stock value metrics — Coming Soon", "Reports / CSV — Coming Soon"].map((item) => (
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

"use client";

import { AuthGate } from "@/components/AuthGate";

export default function DashboardPage() {
  return (
    <AuthGate>
      <section className="max-w-2xl">
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Overview</p>
        <h2 className="mt-2 text-3xl font-semibold">Dashboard</h2>
        <p className="mt-3 text-[var(--muted)] leading-relaxed">
          Live stock value, low-stock alerts, pending POs, and recent movements will appear here.
          Metrics and CRUD are Coming Soon — this shell confirms navigation and demo auth only.
        </p>
        <ul className="mt-8 space-y-3 text-sm">
          {[
            "Stock value — Coming Soon",
            "Low / out-of-stock items — Coming Soon",
            "Pending purchase orders — Coming Soon",
            "Recent movements — Coming Soon",
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

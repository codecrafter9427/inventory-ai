"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getUser } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", enabled: true },
  { href: "/products", label: "Products", enabled: true },
  { href: "/purchase-orders", label: "Purchase orders", enabled: true },
  { href: "/stock", label: "Stock", enabled: true },
  { href: "/reorder", label: "Reorder AI", enabled: true },
  { href: "/stockout-radar", label: "Stockout Radar", enabled: true },
  { href: "/ai-ask", label: "AI Q&A", enabled: true },
  { href: "/transfers", label: "Transfers", enabled: false },
  { href: "/counts", label: "Counts", enabled: false },
  { href: "/suppliers", label: "Suppliers", enabled: false },
  { href: "/locations", label: "Locations", enabled: false },
  { href: "/reports", label: "Reports", enabled: false },
  { href: "/settings", label: "Settings", enabled: false },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  function logout() {
    clearSession();
    router.push("/login");
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="md:w-60 border-b md:border-b-0 md:border-r border-[var(--border)] bg-[var(--bg-elevated)]/90 p-4 flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Portfolio</p>
          <h1 className="text-xl font-semibold tracking-tight text-[var(--accent)]">Inventory AI</h1>
        </div>
        <nav className="flex flex-col gap-1 text-sm">
          {NAV.map((item) => {
            const active = pathname === item.href;
            if (!item.enabled) {
              return (
                <span
                  key={item.href}
                  className="disabled-link flex items-center justify-between rounded px-3 py-2 text-[var(--muted)]"
                  title="Coming Soon"
                >
                  {item.label}
                  <span className="text-[10px] uppercase tracking-wide">Soon</span>
                </span>
              );
            }
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded px-3 py-2 ${active ? "bg-[var(--surface)] text-[var(--accent)]" : "hover:bg-[var(--surface)]"}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto pt-4 border-t border-[var(--border)] text-xs text-[var(--muted)]">
          <p>{user?.displayName ?? "Demo user"}</p>
          <p className="capitalize">{user?.role ?? "guest"}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-2 text-[var(--accent)] hover:underline"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 md:p-8">{children}</main>
    </div>
  );
}

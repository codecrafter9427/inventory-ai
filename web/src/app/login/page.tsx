"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE, saveSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@demo.inventory.local");
  const [password, setPassword] = useState("demo-password");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/demo-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        // Offline / backend-down fallback for shell demos
        saveSession("demo-token-local", {
          email,
          role: "owner",
          displayName: "Demo Owner (offline)",
        });
        router.push("/dashboard");
        return;
      }
      const data = await res.json();
      saveSession(data.access_token, {
        email,
        role: data.role,
        displayName: data.display_name,
      });
      router.push("/dashboard");
    } catch {
      saveSession("demo-token-local", {
        email,
        role: "owner",
        displayName: "Demo Owner (offline)",
      });
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Business portfolio</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight text-[var(--accent)]">
          Inventory AI
        </h1>
        <p className="mt-3 text-[var(--muted)]">
          Demo login shell. Backend optional — offline fallback keeps the UI walkthrough working.
        </p>
        <form
          onSubmit={onSubmit}
          className="mt-8 space-y-4 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)]/80 p-6"
        >
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Email</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 outline-none focus:border-[var(--accent)]"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Password</span>
            <input
              className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 outline-none focus:border-[var(--accent)]"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-[var(--accent-dim)] px-4 py-2.5 font-medium text-white hover:bg-[var(--accent)] disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in (demo)"}
          </button>
        </form>
      </div>
    </div>
  );
}

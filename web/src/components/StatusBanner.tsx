type Props = {
  error?: string | null;
  success?: string | null;
  info?: string | null;
};

export function StatusBanner({ error, success, info }: Props) {
  if (!error && !success && !info) return null;
  return (
    <div className="space-y-2">
      {error ? (
        <p
          role="alert"
          className="rounded border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-3 py-2 text-sm text-[var(--danger)]"
        >
          {error}
        </p>
      ) : null}
      {success ? (
        <p
          role="status"
          className="rounded border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-3 py-2 text-sm text-[var(--accent)]"
        >
          {success}
        </p>
      ) : null}
      {info ? (
        <p className="rounded border border-[var(--border)] bg-[var(--surface)]/60 px-3 py-2 text-sm text-[var(--muted)]">
          {info}
        </p>
      ) : null}
    </div>
  );
}

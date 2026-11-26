type Props = {
  title: string;
  description: string;
};

export function ComingSoon({ title, description }: Props) {
  return (
    <section className="max-w-xl">
      <p className="text-xs uppercase tracking-[0.18em] text-[var(--warn)]">Coming Soon</p>
      <h2 className="mt-2 text-2xl font-semibold">{title}</h2>
      <p className="mt-3 text-[var(--muted)] leading-relaxed">{description}</p>
      <button
        type="button"
        disabled
        className="mt-6 rounded border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm"
      >
        Action disabled
      </button>
    </section>
  );
}

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-5 px-6 text-center">
      <span className="rounded-full border border-black/10 px-3 py-1 text-xs font-medium tracking-wide text-black/60 dark:border-white/15 dark:text-white/60">
        ORIN
      </span>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
        Your knowledge, made conversational
      </h1>
      <p className="max-w-lg text-base leading-relaxed text-black/60 dark:text-white/60">
        Orin is an AI companion that reads your documents and talks with you about them —
        with real citations, and a tone you choose.
      </p>
      <a
        href="/register"
        className="mt-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 dark:bg-accent dark:text-accent-foreground dark:hover:bg-accent/90"
      >
        Get started — it&apos;s free
      </a>
    </main>
  );
}

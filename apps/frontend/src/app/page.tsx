export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
      <span className="rounded-full border border-black/10 px-3 py-1 text-xs font-medium text-black/60 dark:border-white/15 dark:text-white/60">
        SmartSupport AI Platform
      </span>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        Turn your knowledge base into an AI support agent
      </h1>
      <p className="max-w-xl text-base text-black/60 dark:text-white/60">
        Upload your docs. Ask questions. Get accurate, cited answers powered by
        retrieval-augmented generation.
      </p>
      <a
        href="/register"
        className="rounded-lg bg-black px-5 py-2.5 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
      >
        Get started
      </a>
    </main>
  );
}

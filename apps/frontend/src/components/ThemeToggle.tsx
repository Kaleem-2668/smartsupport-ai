"use client";

import { useTheme, type Theme } from "@/context/ThemeContext";

const OPTIONS: { key: Theme; label: string; icon: string }[] = [
  { key: "light", label: "Light", icon: "☀️" },
  { key: "dark", label: "Dark", icon: "🌙" },
  { key: "system", label: "System", icon: "💻" },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className="flex items-center gap-0.5 rounded-lg border border-black/10 p-0.5 dark:border-white/15"
      role="radiogroup"
      aria-label="Theme"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.key}
          type="button"
          role="radio"
          aria-checked={theme === option.key}
          title={option.label}
          onClick={() => setTheme(option.key)}
          className={`flex h-7 w-7 items-center justify-center rounded-md text-sm transition ${
            theme === option.key
              ? "bg-accent/10 dark:bg-accent/15"
              : "opacity-50 hover:opacity-100"
          }`}
        >
          {option.icon}
        </button>
      ))}
    </div>
  );
}

"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

export type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "orin-theme";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  if (theme !== "system") {
    root.classList.add(theme);
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Real value is read from localStorage synchronously here (SSR-safe via the
  // typeof window guard); the inline script in layout.tsx applies the class before
  // paint too, so there's no flash even before this state settles.
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "system";
    const stored = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
    return stored === "light" || stored === "dark" || stored === "system" ? stored : "system";
  });

  function setTheme(next: Theme) {
    setThemeState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

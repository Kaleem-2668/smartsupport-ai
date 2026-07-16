import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ToastProvider } from "@/context/ToastContext";

export const metadata: Metadata = {
  title: "Orin",
  description: "Orin is an AI-powered knowledge companion — upload your documents and get accurate, cited answers powered by retrieval-augmented generation.",
};

// Runs before React hydrates so the correct theme class is on <html> before first
// paint — otherwise a dark-mode user would see a light flash on every load.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem('orin-theme');
    var isDark = stored === 'dark' || (stored !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.classList.toggle('light', stored === 'light');
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col font-sans">
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>{children}</AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

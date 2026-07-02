import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartSupport AI Platform",
  description: "AI-powered customer support built on your own knowledge base.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}

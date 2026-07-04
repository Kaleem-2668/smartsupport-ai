"use client";

import Link from "next/link";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";

function DashboardContent() {
  const { user, logout } = useAuth();

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {user?.full_name || user?.email}</h1>
        <p className="mt-2 text-sm text-black/60 dark:text-white/60">
          This page is protected — it redirects to login if you&apos;re not authenticated.
        </p>
      </div>

      <div className="flex gap-4">
        <Link
          href="/chat"
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
        >
          Open Chat
        </Link>
        <Link
          href="/documents"
          className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
        >
          View Documents
        </Link>
        <Link
          href="/documents/upload"
          className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
        >
          Upload Document
        </Link>
      </div>

      <button
        onClick={logout}
        className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
      >
        Log out
      </button>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}

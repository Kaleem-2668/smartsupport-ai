"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";

function DashboardContent() {
  const { user, logout } = useAuth();

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold">Welcome, {user?.full_name || user?.email}</h1>
      <p className="text-sm text-black/60 dark:text-white/60">
        This page is protected — it redirects to login if you&apos;re not authenticated.
      </p>
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

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/context/AuthContext";
import { getDashboardStats, type DashboardStats } from "@/lib/api/dashboard";

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHrs = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHrs < 24) return `${diffHrs}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function StatCard({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-black/10 bg-white p-5 dark:border-white/15 dark:bg-white/[0.03]">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black/5 text-black/60 dark:bg-white/10 dark:text-white/60">
          {icon}
        </div>
        <div>
          <p className="text-sm text-black/50 dark:text-white/50">{label}</p>
          <p className="text-2xl font-semibold tracking-tight">{value}</p>
          {sub && <p className="text-xs text-black/40 dark:text-white/40">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ready: "bg-green-500",
    processing: "bg-blue-500 animate-pulse",
    error: "bg-red-500",
    uploading: "bg-yellow-500",
  };
  return (
    <span className={`inline-block h-2 w-2 rounded-full ${colors[status] || "bg-gray-400"}`} />
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch {
        setError("Failed to load dashboard stats.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const displayName = user?.full_name || user?.email || "there";

  return (
    <main className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Welcome back, {displayName}
          </h1>
          <p className="mt-1 text-sm text-black/50 dark:text-white/50">
            Here&apos;s an overview of your Orin knowledge base.
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <div className="flex flex-col items-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-black/20 border-t-black dark:border-white/20 dark:border-t-white" />
              <p className="text-sm text-black/50 dark:text-white/50">Loading stats…</p>
            </div>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        ) : stats ? (
          <>
            {/* Stat cards */}
            <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Documents"
                value={stats.documents.total}
                sub={`${formatFileSize(stats.documents.total_size_bytes)} total`}
                icon={
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              />
              <StatCard
                label="Embeddings"
                value={stats.documents.total_chunks.toLocaleString()}
                sub="document chunks"
                icon={
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6M12 9v6" />
                  </svg>
                }
              />
              <StatCard
                label="Knowledge Bases"
                value={stats.knowledge_bases.total}
                sub="active collections"
                icon={
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                }
              />
              <StatCard
                label="Conversations"
                value={stats.conversations.total}
                sub={`${stats.conversations.total_messages.toLocaleString()} messages`}
                icon={
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                }
              />
            </div>

            {/* Document status breakdown */}
            {stats.documents.total > 0 && (
              <div className="mb-8 rounded-xl border border-black/10 bg-white p-5 dark:border-white/15 dark:bg-white/[0.03]">
                <h2 className="mb-4 text-sm font-semibold text-black/70 dark:text-white/70">
                  Document Status
                </h2>
                <div className="flex flex-wrap gap-4">
                  {Object.entries(stats.documents.by_status).map(([status, count]) => (
                    <div key={status} className="flex items-center gap-2">
                      <StatusDot status={status} />
                      <span className="text-sm capitalize text-black/60 dark:text-white/60">
                        {status}
                      </span>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick actions */}
            <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Link
                href="/chat"
                className="group flex items-center gap-3 rounded-xl border border-black/10 bg-white p-4 transition hover:border-black/20 hover:shadow-sm dark:border-white/15 dark:bg-white/[0.03] dark:hover:border-white/25"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground transition group-hover:scale-105 dark:bg-accent dark:text-accent-foreground">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Open Chat</p>
                  <p className="text-xs text-black/40 dark:text-white/40">Ask your knowledge base</p>
                </div>
              </Link>
              <Link
                href="/documents/upload"
                className="group flex items-center gap-3 rounded-xl border border-black/10 bg-white p-4 transition hover:border-black/20 hover:shadow-sm dark:border-white/15 dark:bg-white/[0.03] dark:hover:border-white/25"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground transition group-hover:scale-105 dark:bg-accent dark:text-accent-foreground">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Upload Document</p>
                  <p className="text-xs text-black/40 dark:text-white/40">Add files to your KB</p>
                </div>
              </Link>
              <Link
                href="/knowledge-bases"
                className="group flex items-center gap-3 rounded-xl border border-black/10 bg-white p-4 transition hover:border-black/20 hover:shadow-sm dark:border-white/15 dark:bg-white/[0.03] dark:hover:border-white/25"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground transition group-hover:scale-105 dark:bg-accent dark:text-accent-foreground">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Knowledge Bases</p>
                  <p className="text-xs text-black/40 dark:text-white/40">Organize documents</p>
                </div>
              </Link>
            </div>

            {/* Recent activity */}
            <div className="rounded-xl border border-black/10 bg-white p-5 dark:border-white/15 dark:bg-white/[0.03]">
              <h2 className="mb-4 text-sm font-semibold text-black/70 dark:text-white/70">
                Recent Activity
              </h2>
              {stats.recent_activity.length === 0 ? (
                <p className="py-6 text-center text-sm text-black/40 dark:text-white/40">
                  No activity yet. Upload a document or start a chat to get going.
                </p>
              ) : (
                <ul className="divide-y divide-black/5 dark:divide-white/10">
                  {stats.recent_activity.map((item) => (
                    <li key={`${item.type}-${item.id}`} className="flex items-center gap-3 py-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/5 text-black/50 dark:bg-white/10 dark:text-white/50">
                        {item.type === "document" ? (
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        ) : (
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 truncate">
                        <p className="truncate text-sm font-medium">{item.title}</p>
                        <p className="text-xs capitalize text-black/40 dark:text-white/40">
                          {item.type}
                        </p>
                      </div>
                      <span className="shrink-0 text-xs text-black/40 dark:text-white/40">
                        {formatDate(item.timestamp)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <DashboardContent />
      </AppShell>
    </ProtectedRoute>
  );
}

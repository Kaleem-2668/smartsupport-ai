"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import {
  deleteAdminConversation,
  deleteAdminDocument,
  deleteAdminUser,
  getAdminConversations,
  getAdminDocuments,
  getAdminStats,
  getAdminUsers,
  updateAdminUser,
  type AdminConversation,
  type AdminDocument,
  type AdminStats,
  type AdminUser,
} from "@/lib/api/admin";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-black/10 bg-white p-4 dark:border-white/15 dark:bg-white/[0.03]">
      <p className="text-xs font-medium text-black/50 dark:text-white/50">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function AdminContent() {
  const { showToast } = useToast();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [activeTab, setActiveTab] = useState<"users" | "conversations" | "documents">("users");
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [pendingUserId, setPendingUserId] = useState<string | null>(null);
  const [pendingItemId, setPendingItemId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const [statsData, usersData, conversationsData, documentsData] = await Promise.all([
          getAdminStats(),
          getAdminUsers(),
          getAdminConversations(),
          getAdminDocuments(),
        ]);
        setStats(statsData);
        setUsers(usersData);
        setConversations(conversationsData);
        setDocuments(documentsData);
      } catch {
        showToast("Failed to load admin data.", "error");
      } finally {
        setIsLoading(false);
      }
    }
    load();
    // showToast is stable (from context) — safe to omit from deps here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runSearch(query: string) {
    setSearchQuery(query);
    try {
      setUsers(await getAdminUsers(query || undefined));
    } catch {
      showToast("Search failed.", "error");
    }
  }

  async function handleToggleActive(user: AdminUser) {
    setPendingUserId(user.id);
    try {
      const updated = await updateAdminUser(user.id, { is_active: !user.is_active });
      setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
      showToast(updated.is_active ? "User reactivated." : "User deactivated.", "success");
    } catch {
      showToast("Failed to update user.", "error");
    } finally {
      setPendingUserId(null);
    }
  }

  async function handleToggleRole(user: AdminUser) {
    const nextRole = user.role === "admin" ? "user" : "admin";
    setPendingUserId(user.id);
    try {
      const updated = await updateAdminUser(user.id, { role: nextRole });
      setUsers((prev) => prev.map((u) => (u.id === user.id ? updated : u)));
      showToast(`${updated.email} is now ${nextRole}.`, "success");
    } catch {
      showToast("Failed to update role — you may not be able to change your own.", "error");
    } finally {
      setPendingUserId(null);
    }
  }

  async function handleDelete(user: AdminUser) {
    if (!window.confirm(`Permanently delete ${user.email} and all their data? This can't be undone.`)) {
      return;
    }
    setPendingUserId(user.id);
    try {
      await deleteAdminUser(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
      showToast("User deleted.", "success");
    } catch {
      showToast("Failed to delete user.", "error");
    } finally {
      setPendingUserId(null);
    }
  }

  async function handleDeleteConversation(conversation: AdminConversation) {
    if (!window.confirm(`Delete this conversation from ${conversation.user_email}?`)) return;
    setPendingItemId(conversation.id);
    try {
      await deleteAdminConversation(conversation.id);
      setConversations((prev) => prev.filter((c) => c.id !== conversation.id));
      showToast("Conversation deleted.", "success");
    } catch {
      showToast("Failed to delete conversation.", "error");
    } finally {
      setPendingItemId(null);
    }
  }

  async function handleDeleteDocument(document: AdminDocument) {
    if (!window.confirm(`Delete "${document.original_filename}" (${document.user_email})?`)) return;
    setPendingItemId(document.id);
    try {
      await deleteAdminDocument(document.id);
      setDocuments((prev) => prev.filter((d) => d.id !== document.id));
      showToast("Document deleted.", "success");
    } catch {
      showToast("Failed to delete document.", "error");
    } finally {
      setPendingItemId(null);
    }
  }

  return (
    <main className="flex flex-1 flex-col overflow-y-auto px-4 py-8 sm:px-6">
      <div className="mx-auto w-full max-w-5xl">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Admin</h1>
          <p className="text-sm text-black/60 dark:text-white/60">
            System-wide stats and user management
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded-xl bg-black/5 dark:bg-white/5" />
            ))}
          </div>
        ) : stats ? (
          <>
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Total users" value={stats.total_users} />
              <StatCard label="Active (7d)" value={stats.active_users_7d} />
              <StatCard label="Conversations" value={stats.total_conversations} />
              <StatCard label="Messages" value={stats.total_messages} />
              <StatCard label="Documents" value={stats.total_documents} />
              <StatCard label="Knowledge bases" value={stats.total_knowledge_bases} />
              <StatCard label="Storage used" value={formatBytes(stats.total_storage_bytes)} />
              <StatCard
                label="Top personality"
                value={
                  Object.entries(stats.personality_breakdown).sort((a, b) => b[1] - a[1])[0]?.[0] ??
                  "—"
                }
              />
            </div>

            {stats.most_active_users.length > 0 && (
              <div className="mb-6 rounded-xl border border-black/10 bg-white p-4 dark:border-white/15 dark:bg-white/[0.03]">
                <p className="mb-2 text-sm font-medium">Most active users</p>
                <ul className="space-y-1 text-sm text-black/70 dark:text-white/70">
                  {stats.most_active_users.map((u) => (
                    <li key={u.user_id} className="flex justify-between">
                      <span className="truncate">{u.email}</span>
                      <span className="shrink-0 text-black/50 dark:text-white/50">
                        {u.conversation_count} conversations
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : null}

        <div className="mb-4 flex gap-1 border-b border-black/10 dark:border-white/15">
          {(["users", "conversations", "documents"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 text-sm font-medium capitalize transition ${
                activeTab === tab
                  ? "border-b-2 border-accent text-accent dark:border-accent dark:text-accent"
                  : "text-black/50 hover:text-black dark:text-white/50 dark:hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "users" && (
        <div className="mb-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => runSearch(e.target.value)}
            placeholder="Search users by email or name"
            className="w-full max-w-sm rounded-lg border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white"
          />
        </div>
        )}

        {activeTab === "users" && (
        <div className="overflow-x-auto rounded-xl border border-black/10 dark:border-white/15">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-black/10 bg-black/[0.02] text-xs text-black/50 dark:border-white/15 dark:bg-white/[0.03] dark:text-white/50">
              <tr>
                <th className="px-4 py-2 font-medium">User</th>
                <th className="px-4 py-2 font-medium">Role</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Activity</th>
                <th className="px-4 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5 dark:divide-white/10">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-2.5">
                    <p className="font-medium">{u.full_name || u.email}</p>
                    <p className="text-xs text-black/50 dark:text-white/50">{u.email}</p>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.role === "admin"
                          ? "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400"
                          : "bg-black/5 text-black/60 dark:bg-white/10 dark:text-white/60"
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.is_active
                          ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400"
                          : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400"
                      }`}
                    >
                      {u.is_active ? "active" : "disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-black/60 dark:text-white/60">
                    {u.conversation_count} chats · {u.document_count} docs
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex flex-wrap gap-2 text-xs">
                      <button
                        onClick={() => handleToggleRole(u)}
                        disabled={pendingUserId === u.id}
                        className="font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        {u.role === "admin" ? "Demote" : "Promote"}
                      </button>
                      <button
                        onClick={() => handleToggleActive(u)}
                        disabled={pendingUserId === u.id}
                        className="font-medium text-amber-600 hover:text-amber-700 disabled:opacity-50 dark:text-amber-400 dark:hover:text-amber-300"
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                      <button
                        onClick={() => handleDelete(u)}
                        disabled={pendingUserId === u.id}
                        className="font-medium text-red-600 hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isLoading && users.length === 0 && (
            <p className="p-4 text-center text-sm text-black/50 dark:text-white/50">
              No users match your search.
            </p>
          )}
        </div>
        )}

        {activeTab === "conversations" && (
          <div className="overflow-x-auto rounded-xl border border-black/10 dark:border-white/15">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-black/10 bg-black/[0.02] text-xs text-black/50 dark:border-white/15 dark:bg-white/[0.03] dark:text-white/50">
                <tr>
                  <th className="px-4 py-2 font-medium">Title</th>
                  <th className="px-4 py-2 font-medium">User</th>
                  <th className="px-4 py-2 font-medium">Personality</th>
                  <th className="px-4 py-2 font-medium">Messages</th>
                  <th className="px-4 py-2 font-medium">Updated</th>
                  <th className="px-4 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5 dark:divide-white/10">
                {conversations.map((c) => (
                  <tr key={c.id}>
                    <td className="max-w-[200px] truncate px-4 py-2.5">{c.title || "Untitled"}</td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">{c.user_email}</td>
                    <td className="px-4 py-2.5 capitalize text-black/60 dark:text-white/60">
                      {c.personality}
                    </td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">{c.message_count}</td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">
                      {new Date(c.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => handleDeleteConversation(c)}
                        disabled={pendingItemId === c.id}
                        className="text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!isLoading && conversations.length === 0 && (
              <p className="p-4 text-center text-sm text-black/50 dark:text-white/50">
                No conversations yet.
              </p>
            )}
          </div>
        )}

        {activeTab === "documents" && (
          <div className="overflow-x-auto rounded-xl border border-black/10 dark:border-white/15">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-black/10 bg-black/[0.02] text-xs text-black/50 dark:border-white/15 dark:bg-white/[0.03] dark:text-white/50">
                <tr>
                  <th className="px-4 py-2 font-medium">Filename</th>
                  <th className="px-4 py-2 font-medium">User</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Size</th>
                  <th className="px-4 py-2 font-medium">Uploaded</th>
                  <th className="px-4 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5 dark:divide-white/10">
                {documents.map((d) => (
                  <tr key={d.id}>
                    <td className="max-w-[200px] truncate px-4 py-2.5">{d.original_filename}</td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">{d.user_email}</td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">{d.status}</td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">
                      {formatBytes(d.file_size)}
                    </td>
                    <td className="px-4 py-2.5 text-black/60 dark:text-white/60">
                      {new Date(d.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => handleDeleteDocument(d)}
                        disabled={pendingItemId === d.id}
                        className="text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!isLoading && documents.length === 0 && (
              <p className="p-4 text-center text-sm text-black/50 dark:text-white/50">
                No documents yet.
              </p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default function AdminPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  if (!isLoading && user && user.role !== "admin") {
    return null;
  }

  return (
    <ProtectedRoute>
      <AppShell>
        <AdminContent />
      </AppShell>
    </ProtectedRoute>
  );
}

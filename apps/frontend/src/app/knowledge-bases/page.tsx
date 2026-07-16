"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { useToast } from "@/context/ToastContext";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  getKnowledgeBases,
  type KnowledgeBase,
  type KnowledgeBaseCreate,
} from "@/lib/api/knowledge-bases";

function KnowledgeBasesContent() {
  const { showToast } = useToast();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKbName, setNewKbName] = useState("");
  const [newKbDescription, setNewKbDescription] = useState("");

  useEffect(() => {
    async function loadKnowledgeBases() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getKnowledgeBases();
        setKnowledgeBases(data);
      } catch {
        setError("Failed to load knowledge bases. Please try again.");
      } finally {
        setIsLoading(false);
      }
    }
    loadKnowledgeBases();
  }, []);

  async function handleDelete(knowledgeBaseId: string) {
    setDeletingId(knowledgeBaseId);
    try {
      await deleteKnowledgeBase(knowledgeBaseId);
      setKnowledgeBases((kbs) => kbs.filter((kb) => kb.id !== knowledgeBaseId));
      showToast("Knowledge base deleted.", "success");
    } catch {
      showToast("Failed to delete knowledge base. Please try again.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newKbName.trim()) return;

    setIsCreating(true);
    try {
      const data: KnowledgeBaseCreate = {
        name: newKbName.trim(),
        description: newKbDescription.trim() || undefined,
      };
      const created = await createKnowledgeBase(data);
      setKnowledgeBases((kbs) => [created, ...kbs]);
      setNewKbName("");
      setNewKbDescription("");
      setShowCreateModal(false);
      showToast("Knowledge base created.", "success");
    } catch {
      showToast("Failed to create knowledge base. Please try again.", "error");
    } finally {
      setIsCreating(false);
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  return (
    <main className="flex flex-1 flex-col overflow-y-auto px-4 py-8 sm:px-6">
      <div className="mx-auto w-full max-w-4xl">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Knowledge Bases</h1>
            <p className="text-sm text-black/60 dark:text-white/60">
              Organize your documents into knowledge bases
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center justify-center rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 dark:bg-accent dark:text-accent-foreground dark:hover:bg-accent/90"
          >
            Create Knowledge Base
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="h-20 animate-pulse rounded-lg border border-black/10 bg-black/5 dark:border-white/15 dark:bg-white/5"
              />
            ))}
          </div>
        ) : knowledgeBases.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-black/10 py-12 dark:border-white/15">
            <svg
              className="mb-4 h-12 w-12 text-black/40 dark:text-white/40"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <p className="text-sm text-black/60 dark:text-white/60">No knowledge bases yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 text-sm font-medium text-black underline dark:text-white"
            >
              Create your first knowledge base
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {knowledgeBases.map((kb) => (
              <div
                key={kb.id}
                className="flex flex-col gap-3 rounded-lg border border-black/10 bg-white p-4 dark:border-white/15 dark:bg-black sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex-1">
                  <h3 className="font-medium">{kb.name}</h3>
                  {kb.description && (
                    <p className="mt-1 text-sm text-black/60 dark:text-white/60">{kb.description}</p>
                  )}
                  <p className="mt-2 text-xs text-black/40 dark:text-white/40">
                    Created {formatDate(kb.created_at)}
                  </p>
                </div>
                <div className="flex gap-3">
                  <Link
                    href={`/documents?kb=${kb.id}`}
                    className="text-sm font-medium text-blue-600 transition hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    Manage Documents
                  </Link>
                  <button
                    onClick={() => handleDelete(kb.id)}
                    disabled={deletingId === kb.id}
                    className="text-sm font-medium text-red-600 transition hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                  >
                    {deletingId === kb.id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 dark:bg-white/50">
            <div className="w-full max-w-md rounded-lg border border-black/10 bg-white p-6 shadow-xl dark:border-white/15 dark:bg-black">
              <h2 className="mb-4 text-lg font-semibold">Create Knowledge Base</h2>
              <form onSubmit={handleCreate}>
                <div className="mb-4">
                  <label htmlFor="name" className="mb-1 block text-sm font-medium">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={newKbName}
                    onChange={(e) => setNewKbName(e.target.value)}
                    className="w-full rounded-lg border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white"
                    placeholder="e.g., Product Documentation"
                    required
                  />
                </div>
                <div className="mb-6">
                  <label htmlFor="description" className="mb-1 block text-sm font-medium">
                    Description (optional)
                  </label>
                  <textarea
                    id="description"
                    value={newKbDescription}
                    onChange={(e) => setNewKbDescription(e.target.value)}
                    className="w-full rounded-lg border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white"
                    placeholder="Describe what this knowledge base contains"
                    rows={3}
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    disabled={isCreating}
                    className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/5 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreating || !newKbName.trim()}
                    className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 dark:bg-accent dark:text-accent-foreground dark:hover:bg-accent/90 disabled:opacity-50"
                  >
                    {isCreating ? "Creating…" : "Create"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

export default function KnowledgeBasesPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <KnowledgeBasesContent />
      </AppShell>
    </ProtectedRoute>
  );
}

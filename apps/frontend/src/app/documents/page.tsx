"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { deleteDocument, getDocuments, processDocument, type Document } from "@/lib/api/documents";

function DocumentsContent() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch {
      setError("Failed to load documents. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(documentId: string) {
    setDeletingId(documentId);
    try {
      await deleteDocument(documentId);
      setDocuments((docs) => docs.filter((doc) => doc.id !== documentId));
    } catch {
      setError("Failed to delete document. Please try again.");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleProcess(documentId: string) {
    setProcessingId(documentId);
    setError(null);
    try {
      const processed = await processDocument(documentId);
      setDocuments((docs) => docs.map((doc) => (doc.id === documentId ? processed : doc)));
    } catch {
      setError("Failed to process document. Please try again.");
    } finally {
      setProcessingId(null);
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  return (
    <main className="flex flex-1 flex-col px-6 py-8">
      <div className="mx-auto w-full max-w-4xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Documents</h1>
            <p className="text-sm text-black/60 dark:text-white/60">
              Manage your uploaded documents
            </p>
          </div>
          <Link
            href="/documents/upload"
            className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
          >
            Upload Document
          </Link>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex flex-1 items-center justify-center py-12">
            <p className="text-sm text-black/50 dark:text-white/50">Loading documents…</p>
          </div>
        ) : documents.length === 0 ? (
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-sm text-black/60 dark:text-white/60">No documents uploaded yet</p>
            <Link
              href="/documents/upload"
              className="mt-2 text-sm font-medium text-black underline dark:text-white"
            >
              Upload your first document
            </Link>
          </div>
        ) : (
          <div className="rounded-lg border border-black/10 dark:border-white/15">
            <table className="w-full">
              <thead>
                <tr className="border-b border-black/10 bg-black/5 text-left text-sm dark:border-white/15 dark:bg-white/5">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Uploaded</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Chunks</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr
                    key={document.id}
                    className="border-b border-black/10 text-sm last:border-0 dark:border-white/15"
                  >
                    <td className="px-4 py-3 font-medium">{document.original_filename}</td>
                    <td className="px-4 py-3 text-black/60 dark:text-white/60">
                      {formatFileSize(document.file_size)}
                    </td>
                    <td className="px-4 py-3 text-black/60 dark:text-white/60">
                      {document.mime_type.split("/")[1].toUpperCase()}
                    </td>
                    <td className="px-4 py-3 text-black/60 dark:text-white/60">
                      {formatDate(document.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                          document.status === "ready"
                            ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400"
                            : document.status === "processing"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400"
                            : document.status === "error"
                            ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400"
                            : "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400"
                        }`}
                      >
                        {document.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-black/60 dark:text-white/60">
                      {document.chunk_count ?? "-"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {document.status === "ready" && document.chunk_count === null && (
                          <button
                            onClick={() => handleProcess(document.id)}
                            disabled={processingId === document.id}
                            className="text-sm font-medium text-blue-600 transition hover:text-blue-700 disabled:opacity-50 dark:text-blue-400 dark:hover:text-blue-300"
                          >
                            {processingId === document.id ? "Processing…" : "Process"}
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(document.id)}
                          disabled={deletingId === document.id || processingId === document.id}
                          className="text-sm font-medium text-red-600 transition hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                        >
                          {deletingId === document.id ? "Deleting…" : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute>
      <DocumentsContent />
    </ProtectedRoute>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { useToast } from "@/context/ToastContext";
import {
  deleteDocument,
  getDocuments,
  getRelatedDocuments,
  processDocument,
  type Document,
  type RelatedDocument,
} from "@/lib/api/documents";

const STATUS_STYLES: Record<string, string> = {
  ready: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400",
  processing: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400",
  error: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
  uploading: "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400",
};

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

function DocumentCardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-black/10 bg-white p-4 dark:border-white/15 dark:bg-white/[0.03]">
      <div className="mb-3 h-4 w-3/4 rounded bg-black/10 dark:bg-white/10" />
      <div className="mb-2 h-3 w-1/2 rounded bg-black/10 dark:bg-white/10" />
      <div className="h-3 w-1/3 rounded bg-black/10 dark:bg-white/10" />
    </div>
  );
}

function DocumentCard({
  document,
  isDeleting,
  isProcessing,
  onDelete,
  onProcess,
}: {
  document: Document;
  isDeleting: boolean;
  isProcessing: boolean;
  onDelete: () => void;
  onProcess: () => void;
}) {
  const router = useRouter();
  const [isExpanded, setIsExpanded] = useState(false);
  const [relatedDocuments, setRelatedDocuments] = useState<RelatedDocument[] | null>(null);
  const [isLoadingRelated, setIsLoadingRelated] = useState(false);

  const hasInsights = Boolean(
    document.summary || document.suggested_questions?.length || document.chunk_count
  );

  async function handleToggleExpand() {
    const nextExpanded = !isExpanded;
    setIsExpanded(nextExpanded);
    if (nextExpanded && relatedDocuments === null && document.chunk_count) {
      setIsLoadingRelated(true);
      try {
        const related = await getRelatedDocuments(document.id);
        setRelatedDocuments(related);
      } catch {
        setRelatedDocuments([]);
      } finally {
        setIsLoadingRelated(false);
      }
    }
  }

  function handleAskSuggestedQuestion(question: string) {
    router.push(`/chat?q=${encodeURIComponent(question)}`);
  }

  return (
    <div className="flex flex-col rounded-xl border border-black/10 bg-white p-4 transition hover:border-black/20 hover:shadow-sm dark:border-white/15 dark:bg-white/[0.03] dark:hover:border-white/25">
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-black/5 text-black/60 dark:bg-white/10 dark:text-white/60">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium" title={document.original_filename}>
            {document.original_filename}
          </p>
          <p className="text-xs text-black/50 dark:text-white/50">
            {formatFileSize(document.file_size)} · {document.mime_type.split("/")[1].toUpperCase()}
          </p>
        </div>
        <span
          className={`inline-flex shrink-0 rounded-full px-2 py-1 text-xs font-medium ${
            STATUS_STYLES[document.status] || "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400"
          }`}
        >
          {document.status}
        </span>
      </div>

      <div className="mb-4 flex items-center gap-3 text-xs text-black/50 dark:text-white/50">
        <span>Uploaded {formatDate(document.created_at)}</span>
        {document.chunk_count !== null && (
          <>
            <span aria-hidden="true">·</span>
            <span>{document.chunk_count.toLocaleString()} chunks</span>
          </>
        )}
      </div>

      {hasInsights && (
        <div className="mb-3">
          <button
            onClick={handleToggleExpand}
            className="flex items-center gap-1 text-xs font-medium text-black/60 transition hover:text-black dark:text-white/60 dark:hover:text-white"
            aria-expanded={isExpanded}
          >
            <svg
              className={`h-3 w-3 shrink-0 transition-transform ${isExpanded ? "rotate-90" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {isExpanded ? "Hide insights" : "Show insights"}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-3 rounded-lg bg-black/[0.02] p-3 text-xs dark:bg-white/[0.03]">
              {document.summary && (
                <div>
                  <p className="mb-1 font-medium text-black/70 dark:text-white/70">Summary</p>
                  <p className="text-black/60 dark:text-white/60">{document.summary}</p>
                </div>
              )}

              {document.suggested_questions && document.suggested_questions.length > 0 && (
                <div>
                  <p className="mb-1.5 font-medium text-black/70 dark:text-white/70">
                    Suggested questions
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {document.suggested_questions.map((question) => (
                      <button
                        key={question}
                        onClick={() => handleAskSuggestedQuestion(question)}
                        className="rounded-full border border-black/10 px-2.5 py-1 text-left transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="mb-1.5 font-medium text-black/70 dark:text-white/70">
                  Related documents
                </p>
                {isLoadingRelated ? (
                  <p className="text-black/50 dark:text-white/50">Loading…</p>
                ) : relatedDocuments && relatedDocuments.length > 0 ? (
                  <ul className="space-y-1">
                    {relatedDocuments.map((related) => (
                      <li
                        key={related.document_id}
                        className="flex items-center justify-between gap-2 text-black/60 dark:text-white/60"
                      >
                        <span className="truncate">{related.filename}</span>
                        <span className="shrink-0 text-black/40 dark:text-white/40">
                          {Math.round(related.similarity * 100)}% similar
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-black/50 dark:text-white/50">
                    {document.chunk_count
                      ? "No related documents found."
                      : "Process this document to find related ones."}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-auto flex gap-4 border-t border-black/5 pt-3 dark:border-white/10">
        {document.status === "ready" && document.chunk_count === null && (
          <button
            onClick={onProcess}
            disabled={isProcessing}
            className="text-sm font-medium text-blue-600 transition hover:text-blue-700 disabled:opacity-50 dark:text-blue-400 dark:hover:text-blue-300"
          >
            {isProcessing ? "Processing…" : "Process"}
          </button>
        )}
        <button
          onClick={onDelete}
          disabled={isDeleting || isProcessing}
          className="text-sm font-medium text-red-600 transition hover:text-red-700 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
        >
          {isDeleting ? "Deleting…" : "Delete"}
        </button>
      </div>
    </div>
  );
}

function DocumentsContent() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
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
    loadDocuments();
  }, []);

  async function handleDelete(documentId: string) {
    setDeletingId(documentId);
    try {
      await deleteDocument(documentId);
      setDocuments((docs) => docs.filter((doc) => doc.id !== documentId));
      showToast("Document deleted.", "success");
    } catch {
      showToast("Failed to delete document. Please try again.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleProcess(documentId: string) {
    setProcessingId(documentId);
    try {
      const processed = await processDocument(documentId);
      setDocuments((docs) => docs.map((doc) => (doc.id === documentId ? processed : doc)));
      showToast("Document processed successfully.", "success");
    } catch {
      showToast("Failed to process document. Please try again.", "error");
    } finally {
      setProcessingId(null);
    }
  }

  return (
    <main className="flex flex-1 flex-col overflow-y-auto px-4 py-8 sm:px-6">
      <div className="mx-auto w-full max-w-5xl">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Documents</h1>
            <p className="text-sm text-black/60 dark:text-white/60">
              Manage your uploaded documents
            </p>
          </div>
          <Link
            href="/documents/upload"
            className="inline-flex items-center justify-center rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
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
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <DocumentCardSkeleton key={i} />
            ))}
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
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {documents.map((document) => (
              <DocumentCard
                key={document.id}
                document={document}
                isDeleting={deletingId === document.id}
                isProcessing={processingId === document.id}
                onDelete={() => handleDelete(document.id)}
                onProcess={() => handleProcess(document.id)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <DocumentsContent />
      </AppShell>
    </ProtectedRoute>
  );
}

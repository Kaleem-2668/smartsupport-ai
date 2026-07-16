"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type DragEvent, type ChangeEvent } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { useToast } from "@/context/ToastContext";
import { getKnowledgeBases, uploadDocument, type KnowledgeBase } from "@/lib/api";

function UploadPageContent() {
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const kbIdParam = searchParams.get("kb");
  
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState<string | null>(kbIdParam);
  const [isLoadingKbs, setIsLoadingKbs] = useState(false);

  useEffect(() => {
    async function loadKnowledgeBases() {
      setIsLoadingKbs(true);
      try {
        const data = await getKnowledgeBases();
        setKnowledgeBases(data);
      } catch {
        // Non-critical error, continue without knowledge bases
      } finally {
        setIsLoadingKbs(false);
      }
    }
    loadKnowledgeBases();
  }, []);

  const handleDragOver = (event: DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event: DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const allowedTypes = [
      "application/pdf",
      "text/plain",
      "text/markdown",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(selectedFile.type)) {
      setError("File type not supported. Please upload PDF, TXT, MD, DOC, or DOCX files.");
      return;
    }

    if (selectedFile.size > maxSize) {
      setError("File size exceeds 10MB limit.");
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      await uploadDocument(file, selectedKbId || undefined);
      showToast("Document uploaded successfully.", "success");
      router.push("/documents");
    } catch {
      setError("Failed to upload document. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <ProtectedRoute>
      <AppShell>
        <main className="flex flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-8 sm:px-6">
          <div className="w-full max-w-md">
          <h1 className="mb-1 text-2xl font-semibold">Upload Document</h1>
          <p className="mb-6 text-sm text-black/60 dark:text-white/60">
            Upload PDF, TXT, MD, DOC, or DOCX files (max 10MB)
          </p>

          <div
            className={`relative mb-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              isDragging
                ? "border-black/30 bg-black/5 dark:border-white/30 dark:bg-white/10"
                : "border-black/10 dark:border-white/15"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              id="file-upload"
              type="file"
              className="absolute inset-0 cursor-pointer opacity-0"
              onChange={handleFileSelect}
              accept=".pdf,.txt,.md,.doc,.docx"
            />
            <div className="flex flex-col items-center gap-2 text-center">
              <svg
                className="h-12 w-12 text-black/40 dark:text-white/40"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-sm text-black/60 dark:text-white/60">
                {file ? file.name : "Drag and drop or click to upload"}
              </p>
            </div>
          </div>

          {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

          {knowledgeBases.length > 0 && (
            <div className="mb-4">
              <label htmlFor="knowledge-base" className="mb-1 block text-sm font-medium">
                Knowledge Base (optional)
              </label>
              <select
                id="knowledge-base"
                value={selectedKbId || ""}
                onChange={(e) => setSelectedKbId(e.target.value || null)}
                disabled={isLoadingKbs}
                className="w-full rounded-lg border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white disabled:opacity-50"
              >
                <option value="">No knowledge base (default)</option>
                {knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.id}>
                    {kb.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {file && (
            <div className="mb-4 rounded-lg bg-black/5 p-3 dark:bg-white/10">
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-black/60 dark:text-white/60">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-50 dark:bg-accent dark:text-accent-foreground dark:hover:bg-accent/90"
          >
            {isUploading ? "Uploading..." : "Upload Document"}
          </button>

          <p className="mt-6 text-center text-sm text-black/60 dark:text-white/60">
            <Link href="/documents" className="font-medium text-black underline dark:text-white">
              View your documents
            </Link>
          </p>
        </div>
      </main>
      </AppShell>
    </ProtectedRoute>
  );
}

export default function UploadPage() {
  return (
    <Suspense fallback={null}>
      <UploadPageContent />
    </Suspense>
  );
}

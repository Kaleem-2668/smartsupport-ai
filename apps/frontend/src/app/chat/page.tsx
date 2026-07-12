"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/AppShell";
import { useToast } from "@/context/ToastContext";
import {
  askQuestion,
  deleteConversation,
  getConversationMessages,
  getConversations,
  PERSONALITY_OPTIONS,
  renameConversation,
  updateConversationPersonality,
  type Conversation,
  type Message,
  type Personality,
  type Source,
} from "@/lib/api/chat";
import { getKnowledgeBases, type KnowledgeBase } from "@/lib/api/knowledge-bases";

function SourceCitations({ sources }: { sources: Source[] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-2 border-t border-current/10 pt-2">
      <button
        onClick={() => setIsExpanded((open) => !open)}
        className="flex items-center gap-1 text-xs font-medium opacity-70 transition hover:opacity-100"
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
        {sources.length} source{sources.length === 1 ? "" : "s"}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, i) => (
            <div
              key={`${source.document_id}-${source.chunk_index}-${i}`}
              className="rounded-lg border border-current/10 bg-current/[0.03] p-2 text-xs"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium" title={source.document_name}>
                  {source.document_name}
                </span>
                {source.confidence !== null && (
                  <span className="shrink-0 rounded-full bg-current/10 px-1.5 py-0.5 text-[10px] font-medium">
                    {Math.round(source.confidence * 100)}% match
                  </span>
                )}
              </div>
              {source.page_number !== null && (
                <p className="mt-0.5 opacity-60">Page {source.page_number}</p>
              )}
              <p className="mt-1 italic opacity-70">
                &ldquo;{source.snippet}
                {source.snippet.length >= 200 ? "…" : ""}&rdquo;
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PersonalitySelector({
  value,
  onChange,
  disabled,
}: {
  value: Personality;
  onChange: (personality: Personality) => void;
  disabled?: boolean;
}) {
  const [pendingRoastConfirm, setPendingRoastConfirm] = useState(false);

  function handleSelect(key: Personality) {
    if (key === "roast" && key !== value) {
      setPendingRoastConfirm(true);
      return;
    }
    onChange(key);
  }

  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {PERSONALITY_OPTIONS.map((option) => (
          <button
            key={option.key}
            type="button"
            disabled={disabled}
            onClick={() => handleSelect(option.key)}
            title={option.description}
            className={`rounded-full border px-2.5 py-1 text-xs font-medium transition disabled:opacity-50 ${
              value === option.key
                ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
                : "border-black/10 hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
            }`}
          >
            {option.emoji} {option.label}
          </button>
        ))}
      </div>
      {pendingRoastConfirm && (
        <div className="mt-2 rounded-lg border border-orange-300 bg-orange-50 p-2 text-xs text-orange-800 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-300">
          <p className="mb-2">
            Roast Mode is sarcastic and teasing — it still fully answers your question, just
            with attitude. Turn it on?
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                onChange("roast");
                setPendingRoastConfirm(false);
              }}
              className="rounded-md bg-orange-600 px-2 py-1 font-medium text-white transition hover:bg-orange-700"
            >
              Enable Roast Mode
            </button>
            <button
              type="button"
              onClick={() => setPendingRoastConfirm(false)}
              className="rounded-md border border-orange-300 px-2 py-1 font-medium transition hover:bg-orange-100 dark:border-orange-800 dark:hover:bg-orange-900"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ChatContent() {
  const { showToast } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const searchParams = useSearchParams();
  const [input, setInput] = useState(() => searchParams.get("q") || "");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState<string | null>(null);
  const [isLoadingKbs, setIsLoadingKbs] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [newConversationPersonality, setNewConversationPersonality] =
    useState<Personality>("professional");

  useEffect(() => {
    loadConversations();
    loadKnowledgeBases();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadConversations() {
    setIsLoadingConversations(true);
    try {
      const data = await getConversations();
      setConversations(data);
    } catch {
      setError("Failed to load conversations.");
    } finally {
      setIsLoadingConversations(false);
    }
  }

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

  async function handleSelectConversation(conversationId: string) {
    setActiveConversationId(conversationId);
    setIsLoadingMessages(true);
    setError(null);
    setIsSidebarOpen(false);
    try {
      const data = await getConversationMessages(conversationId);
      setMessages(data);
    } catch {
      setError("Failed to load messages.");
    } finally {
      setIsLoadingMessages(false);
    }
  }

  function handleNewConversation() {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
    setIsSidebarOpen(false);
  }

  async function handleDeleteConversation(conversationId: string) {
    try {
      await deleteConversation(conversationId);
      setConversations((convos) => convos.filter((c) => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        handleNewConversation();
      }
      showToast("Conversation deleted.", "success");
    } catch {
      showToast("Failed to delete conversation.", "error");
    }
  }

  async function handleChangePersonality(personality: Personality) {
    if (!activeConversationId) {
      setNewConversationPersonality(personality);
      return;
    }
    try {
      const updated = await updateConversationPersonality(activeConversationId, personality);
      setConversations((convos) =>
        convos.map((c) => (c.id === activeConversationId ? updated : c))
      );
      showToast(`Switched to ${personality} mode.`, "success");
    } catch {
      showToast("Failed to change personality. Please try again.", "error");
    }
  }

  function startRenaming(conversation: Conversation) {
    setEditingConversationId(conversation.id);
    setEditingTitle(conversation.title || "New conversation");
  }

  function cancelRenaming() {
    setEditingConversationId(null);
    setEditingTitle("");
  }

  async function saveRenaming(conversationId: string) {
    const title = editingTitle.trim();
    if (!title) {
      cancelRenaming();
      return;
    }
    try {
      const updated = await renameConversation(conversationId, title);
      setConversations((convos) =>
        convos.map((c) => (c.id === conversationId ? updated : c))
      );
      showToast("Conversation renamed.", "success");
    } catch {
      showToast("Failed to rename conversation.", "error");
    } finally {
      cancelRenaming();
    }
  }

  async function handleSend() {
    const question = input.trim();
    if (!question || isSending) return;

    setInput("");
    setError(null);
    setIsSending(true);

    const optimisticUserMessage: Message = {
      id: `pending-${Date.now()}`,
      conversation_id: activeConversationId ?? "",
      role: "user",
      content: question,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);

    try {
      const response = await askQuestion(
        question,
        activeConversationId,
        selectedKbId || undefined,
        newConversationPersonality
      );
      const isNewConversation = activeConversationId === null;
      setActiveConversationId(response.conversation_id);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUserMessage.id),
        { ...optimisticUserMessage, conversation_id: response.conversation_id },
        response.message,
      ]);
      if (isNewConversation) {
        await loadConversations();
      }
    } catch {
      setError("Failed to get a response. Please try again.");
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMessage.id));
      setInput(question);
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  function formatConversationLabel(conversation: Conversation): string {
    return conversation.title || "New conversation";
  }

  const filteredConversations = conversations.filter((conversation) =>
    formatConversationLabel(conversation).toLowerCase().includes(searchQuery.trim().toLowerCase())
  );

  const activeConversation = conversations.find((c) => c.id === activeConversationId) || null;

  return (
    <main className="relative flex flex-1 overflow-hidden">
      {/* Mobile overlay backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 sm:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-black/10 bg-white transition-transform dark:border-white/15 dark:bg-black sm:static sm:z-auto sm:w-64 sm:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-4">
          <button
            onClick={handleNewConversation}
            className="w-full rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
          >
            New chat
          </button>
        </div>
        {knowledgeBases.length > 0 && (
          <div className="px-4 pb-4">
            <label htmlFor="kb-select" className="mb-1 block text-xs font-medium text-black/60 dark:text-white/60">
              Knowledge Base
            </label>
            <select
              id="kb-select"
              value={selectedKbId || ""}
              onChange={(e) => setSelectedKbId(e.target.value || null)}
              disabled={isLoadingKbs}
              className="w-full rounded-lg border border-black/10 px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white disabled:opacity-50"
            >
              <option value="">All documents</option>
              {knowledgeBases.map((kb) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="px-4 pb-3">
          <div className="relative">
            <svg
              className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-black/40 dark:text-white/40"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-4.35-4.35M17 10.5a6.5 6.5 0 11-13 0 6.5 6.5 0 0113 0z"
              />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations"
              className="w-full rounded-lg border border-black/10 py-1.5 pl-8 pr-3 text-xs focus:outline-none focus:ring-2 focus:ring-black dark:border-white/15 dark:bg-white/5 dark:focus:ring-white"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {isLoadingConversations ? (
            <div className="space-y-2 px-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-9 animate-pulse rounded-lg bg-black/5 dark:bg-white/5" />
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <p className="px-2 text-sm text-black/50 dark:text-white/50">No conversations yet</p>
          ) : filteredConversations.length === 0 ? (
            <p className="px-2 text-sm text-black/50 dark:text-white/50">
              No conversations match &ldquo;{searchQuery}&rdquo;
            </p>
          ) : (
            <ul className="space-y-1">
              {filteredConversations.map((conversation) => (
                <li key={conversation.id} className="group flex items-center gap-1">
                  {editingConversationId === conversation.id ? (
                    <input
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={() => saveRenaming(conversation.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveRenaming(conversation.id);
                        if (e.key === "Escape") cancelRenaming();
                      }}
                      className="flex-1 rounded-lg border border-black/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:border-white/25 dark:bg-white/5 dark:focus:ring-white"
                    />
                  ) : (
                    <button
                      onClick={() => handleSelectConversation(conversation.id)}
                      className={`flex-1 truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                        activeConversationId === conversation.id
                          ? "bg-black/10 dark:bg-white/15"
                          : "hover:bg-black/5 dark:hover:bg-white/10"
                      }`}
                    >
                      {formatConversationLabel(conversation)}
                    </button>
                  )}
                  {editingConversationId !== conversation.id && (
                    <>
                      <button
                        onClick={() => startRenaming(conversation)}
                        className="px-1.5 text-xs text-black/40 opacity-100 transition-opacity hover:text-black sm:opacity-0 sm:group-hover:opacity-100 dark:text-white/40 dark:hover:text-white"
                        aria-label="Rename conversation"
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => handleDeleteConversation(conversation.id)}
                        className="px-1.5 text-xs text-black/40 opacity-100 transition-opacity hover:text-red-600 sm:opacity-0 sm:group-hover:opacity-100 dark:text-white/40 dark:hover:text-red-400"
                        aria-label="Delete conversation"
                      >
                        ✕
                      </button>
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile conversations toggle */}
        <div className="flex items-center justify-between border-b border-black/10 px-4 py-2 dark:border-white/15 sm:hidden">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-black/70 hover:bg-black/5 dark:text-white/70 dark:hover:bg-white/10"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            Conversations
          </button>
        </div>

        {/* Personality selector */}
        <div className="border-b border-black/10 px-4 py-2.5 dark:border-white/15">
          <PersonalitySelector
            value={activeConversation?.personality ?? newConversationPersonality}
            onChange={handleChangePersonality}
            disabled={isSending}
          />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
            {isLoadingMessages ? (
              <p className="text-center text-sm text-black/50 dark:text-white/50">Loading…</p>
            ) : messages.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center py-24 text-center">
                <h1 className="text-xl font-semibold">Ask about your knowledge base</h1>
                <p className="mt-2 text-sm text-black/60 dark:text-white/60">
                  Answers are generated from the documents you&apos;ve uploaded and processed.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                      message.role === "user"
                        ? "bg-black text-white dark:bg-white dark:text-black"
                        : "border border-black/10 dark:border-white/15"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <SourceCitations sources={message.sources} />
                    )}
                  </div>
                </div>
              ))
            )}
            {isSending && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg border border-black/10 px-4 py-2 text-sm text-black/50 dark:border-white/15 dark:text-white/50">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {error && (
          <div className="mx-6 mb-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        <div className="border-t border-black/10 px-6 py-4 dark:border-white/15">
          <div className="mx-auto flex w-full max-w-2xl gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question…"
              rows={1}
              className="flex-1 resize-none rounded-lg border border-black/10 bg-transparent px-4 py-2 text-sm outline-none focus:border-black/30 dark:border-white/15 dark:focus:border-white/40"
            />
            <button
              onClick={handleSend}
              disabled={isSending || !input.trim()}
              className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 disabled:opacity-50 dark:bg-white dark:text-black dark:hover:bg-white/80"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <Suspense fallback={null}>
          <ChatContent />
        </Suspense>
      </AppShell>
    </ProtectedRoute>
  );
}

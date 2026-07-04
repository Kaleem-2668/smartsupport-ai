"use client";

import { useEffect, useRef, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import {
  askQuestion,
  deleteConversation,
  getConversationMessages,
  getConversations,
  type Conversation,
  type Message,
} from "@/lib/api/chat";

function ChatContent() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
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

  async function handleSelectConversation(conversationId: string) {
    setActiveConversationId(conversationId);
    setIsLoadingMessages(true);
    setError(null);
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
  }

  async function handleDeleteConversation(conversationId: string) {
    try {
      await deleteConversation(conversationId);
      setConversations((convos) => convos.filter((c) => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        handleNewConversation();
      }
    } catch {
      setError("Failed to delete conversation.");
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
      const response = await askQuestion(question, activeConversationId);
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

  return (
    <main className="flex flex-1 overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-black/10 dark:border-white/15">
        <div className="p-4">
          <button
            onClick={handleNewConversation}
            className="w-full rounded-lg bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
          >
            New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {isLoadingConversations ? (
            <p className="px-2 text-sm text-black/50 dark:text-white/50">Loading…</p>
          ) : conversations.length === 0 ? (
            <p className="px-2 text-sm text-black/50 dark:text-white/50">No conversations yet</p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conversation) => (
                <li key={conversation.id} className="group flex items-center gap-1">
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
                  <button
                    onClick={() => handleDeleteConversation(conversation.id)}
                    className="hidden px-2 text-xs text-black/40 hover:text-red-600 group-hover:block dark:text-white/40 dark:hover:text-red-400"
                    aria-label="Delete conversation"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex flex-1 flex-col">
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
                      <p className="mt-2 text-xs opacity-60">
                        Sourced from {message.sources.length} document chunk
                        {message.sources.length === 1 ? "" : "s"}
                      </p>
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
      <ChatContent />
    </ProtectedRoute>
  );
}

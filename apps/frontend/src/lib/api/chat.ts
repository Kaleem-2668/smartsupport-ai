import { API_URL, apiClient } from "./client";
import { getStoredTokens } from "./tokenStorage";

export type Personality = "professional" | "tutor" | "friendly" | "playful" | "roast";

export interface PersonalityOption {
  key: Personality;
  label: string;
  emoji: string;
  description: string;
  isOptIn?: boolean;
}

export const PERSONALITY_OPTIONS: PersonalityOption[] = [
  {
    key: "professional",
    label: "Professional",
    emoji: "💼",
    description: "Clear, concise, and factual.",
  },
  {
    key: "tutor",
    label: "Tutor",
    emoji: "🎓",
    description: "Patient, step-by-step explanations.",
  },
  {
    key: "friendly",
    label: "Friendly",
    emoji: "😊",
    description: "Warm and conversational.",
  },
  {
    key: "playful",
    label: "Playful",
    emoji: "✨",
    description: "Upbeat, with a bit of fun.",
  },
  {
    key: "roast",
    label: "Roast",
    emoji: "🔥",
    description: "Sarcastic and teasing, but still accurate.",
    isOptIn: true,
  },
];

export interface Source {
  document_id: string;
  document_name: string;
  chunk_index: number;
  page_number: number | null;
  confidence: number | null;
  snippet: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  personality: Personality;
  created_at: string;
  updated_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
}

export async function askQuestion(
  question: string,
  conversationId?: string | null,
  knowledgeBaseId?: string | null,
  personality?: Personality | null
): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/chat", {
    question,
    conversation_id: conversationId ?? undefined,
    knowledge_base_id: knowledgeBaseId ?? undefined,
    // Only meaningful when starting a new conversation; the backend ignores it
    // for an existing one.
    personality: conversationId ? undefined : personality ?? undefined,
  });
  return data;
}

export interface StreamCallbacks {
  onStart?: (conversationId: string) => void;
  onToken: (token: string) => void;
  onDone: (message: Message) => void;
  onError: (detail: string) => void;
  onAbort?: () => void;
}

export async function askQuestionStream(
  question: string,
  conversationId: string | null | undefined,
  knowledgeBaseId: string | null | undefined,
  personality: Personality | null | undefined,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const { accessToken } = getStoredTokens();

  let response: Response;
  try {
    response = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({
        question,
        conversation_id: conversationId ?? undefined,
        knowledge_base_id: knowledgeBaseId ?? undefined,
        // Only meaningful when starting a new conversation; the backend ignores it
        // for an existing one.
        personality: conversationId ? undefined : personality ?? undefined,
      }),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      callbacks.onAbort?.();
      return;
    }
    callbacks.onError("Network error — couldn't reach the server.");
    return;
  }

  if (!response.ok || !response.body) {
    callbacks.onError(`Request failed (${response.status}).`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by a blank line; the trailing piece may be a partial
      // event still being streamed in, so keep it in the buffer for the next read.
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const dataLine = part.split("\n").find((line) => line.startsWith("data: "));
        if (!dataLine) continue;

        let event: { type: string; conversation_id?: string; content?: string; message?: Message; detail?: string };
        try {
          event = JSON.parse(dataLine.slice("data: ".length));
        } catch {
          continue;
        }

        if (event.type === "start" && event.conversation_id) {
          callbacks.onStart?.(event.conversation_id);
        } else if (event.type === "token" && event.content !== undefined) {
          callbacks.onToken(event.content);
        } else if (event.type === "done" && event.message) {
          callbacks.onDone(event.message);
        } else if (event.type === "error") {
          callbacks.onError(event.detail || "Something went wrong.");
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      callbacks.onAbort?.();
    } else {
      callbacks.onError("Connection lost while streaming the response.");
    }
  }
}

export async function getConversations(): Promise<Conversation[]> {
  const { data } = await apiClient.get<Conversation[]>("/conversations");
  return data;
}

export async function getConversationMessages(conversationId: string): Promise<Message[]> {
  const { data } = await apiClient.get<Message[]>(`/conversations/${conversationId}/messages`);
  return data;
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/conversations/${conversationId}`);
}

export async function renameConversation(
  conversationId: string,
  title: string
): Promise<Conversation> {
  const { data } = await apiClient.patch<Conversation>(`/conversations/${conversationId}`, {
    title,
  });
  return data;
}

export async function updateConversationPersonality(
  conversationId: string,
  personality: Personality
): Promise<Conversation> {
  const { data } = await apiClient.patch<Conversation>(`/conversations/${conversationId}`, {
    personality,
  });
  return data;
}

import { apiClient } from "./client";

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

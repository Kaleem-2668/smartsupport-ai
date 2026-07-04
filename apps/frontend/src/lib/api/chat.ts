import { apiClient } from "./client";

export interface Source {
  document_id: string;
  chunk_index: number;
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
  knowledgeBaseId?: string | null
): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/chat", {
    question,
    conversation_id: conversationId ?? undefined,
    knowledge_base_id: knowledgeBaseId ?? undefined,
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

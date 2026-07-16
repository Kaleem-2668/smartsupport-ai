import { apiClient } from "./client";
import type { User } from "./auth";

export interface MostActiveUser {
  user_id: string;
  email: string;
  conversation_count: number;
}

export interface AdminStats {
  total_users: number;
  active_users_7d: number;
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  total_knowledge_bases: number;
  total_storage_bytes: number;
  personality_breakdown: Record<string, number>;
  most_active_users: MostActiveUser[];
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  role: User["role"];
  created_at: string;
  conversation_count: number;
  document_count: number;
}

export interface AdminConversation {
  id: string;
  user_id: string;
  user_email: string;
  title: string | null;
  personality: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminDocument {
  id: string;
  user_id: string;
  user_email: string;
  original_filename: string;
  status: string;
  file_size: number;
  created_at: string;
}

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await apiClient.get<AdminStats>("/admin/stats");
  return data;
}

export async function getAdminUsers(search?: string): Promise<AdminUser[]> {
  const { data } = await apiClient.get<AdminUser[]>("/admin/users", {
    params: search ? { search } : undefined,
  });
  return data;
}

export async function updateAdminUser(
  userId: string,
  update: { role?: User["role"]; is_active?: boolean }
): Promise<AdminUser> {
  const { data } = await apiClient.patch<AdminUser>(`/admin/users/${userId}`, update);
  return data;
}

export async function deleteAdminUser(userId: string): Promise<void> {
  await apiClient.delete(`/admin/users/${userId}`);
}

export async function getAdminConversations(): Promise<AdminConversation[]> {
  const { data } = await apiClient.get<AdminConversation[]>("/admin/conversations");
  return data;
}

export async function deleteAdminConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/admin/conversations/${conversationId}`);
}

export async function getAdminDocuments(): Promise<AdminDocument[]> {
  const { data } = await apiClient.get<AdminDocument[]>("/admin/documents");
  return data;
}

export async function deleteAdminDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/admin/documents/${documentId}`);
}

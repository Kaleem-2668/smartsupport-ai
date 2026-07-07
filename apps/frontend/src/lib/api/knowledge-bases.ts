import { apiClient } from "./client";

export interface KnowledgeBase {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string;
}

export async function getKnowledgeBases(): Promise<KnowledgeBase[]> {
  const { data } = await apiClient.get<KnowledgeBase[]>("/knowledge-bases");
  return data;
}

export async function getKnowledgeBase(knowledgeBaseId: string): Promise<KnowledgeBase> {
  const { data } = await apiClient.get<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`);
  return data;
}

export async function createKnowledgeBase(payload: KnowledgeBaseCreate): Promise<KnowledgeBase> {
  const { data } = await apiClient.post<KnowledgeBase>("/knowledge-bases", payload);
  return data;
}

export async function updateKnowledgeBase(
  knowledgeBaseId: string,
  payload: KnowledgeBaseUpdate
): Promise<KnowledgeBase> {
  const { data } = await apiClient.patch<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`, payload);
  return data;
}

export async function deleteKnowledgeBase(knowledgeBaseId: string): Promise<void> {
  await apiClient.delete(`/knowledge-bases/${knowledgeBaseId}`);
}

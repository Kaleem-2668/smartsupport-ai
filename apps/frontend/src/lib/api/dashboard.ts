import { apiClient } from "./client";

export interface DocumentStats {
  total: number;
  by_status: Record<string, number>;
  total_chunks: number;
  total_size_bytes: number;
}

export interface KnowledgeBaseStats {
  total: number;
}

export interface ConversationStats {
  total: number;
  total_messages: number;
}

export interface RecentActivity {
  id: string;
  type: string;
  title: string;
  timestamp: string;
}

export interface DashboardStats {
  documents: DocumentStats;
  knowledge_bases: KnowledgeBaseStats;
  conversations: ConversationStats;
  recent_activity: RecentActivity[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/dashboard/stats");
  return data;
}

import { apiClient } from "./client";

export interface Document {
  id: string;
  user_id: string;
  knowledge_base_id: string | null;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  status: string;
  error_message: string | null;
  chunk_count: number | null;
  summary: string | null;
  suggested_questions: string[] | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RelatedDocument {
  document_id: string;
  filename: string;
  similarity: number;
}

export async function uploadDocument(file: File, knowledgeBaseId?: string): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  if (knowledgeBaseId) {
    formData.append("knowledge_base_id", knowledgeBaseId);
  }

  const { data } = await apiClient.post<Document>("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function getDocuments(): Promise<Document[]> {
  const { data } = await apiClient.get<Document[]>("/documents");
  return data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const { data } = await apiClient.get<Document>(`/documents/${documentId}`);
  return data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}

export async function processDocument(documentId: string): Promise<Document> {
  const { data } = await apiClient.post<Document>(`/documents/${documentId}/process`);
  return data;
}

export async function getRelatedDocuments(documentId: string): Promise<RelatedDocument[]> {
  const { data } = await apiClient.get<RelatedDocument[]>(`/documents/${documentId}/related`);
  return data;
}

import { apiClient } from "./client";

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

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

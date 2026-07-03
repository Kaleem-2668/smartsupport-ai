import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function registerUser(
  email: string,
  password: string,
  fullName?: string
): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", {
    email,
    password,
    full_name: fullName || undefined,
  });
  return data;
}

export async function loginUser(email: string, password: string): Promise<AuthTokens> {
  const { data } = await apiClient.post<AuthTokens>("/auth/login", { email, password });
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

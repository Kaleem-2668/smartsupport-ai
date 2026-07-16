import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { clearStoredTokens, getStoredTokens, setStoredTokens } from "./tokenStorage";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export { API_URL };

// Requests to these paths must never trigger the refresh-and-retry flow below —
// a 401 there means "wrong credentials" or "bad token", not "token expired".
const AUTH_PATHS_EXCLUDED_FROM_REFRESH = ["/auth/login", "/auth/register", "/auth/refresh"];

export const apiClient: AxiosInstance = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const { accessToken } = getStoredTokens();
  if (accessToken) {
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return config;
});

let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    const isExcluded = AUTH_PATHS_EXCLUDED_FROM_REFRESH.some((path) =>
      originalRequest?.url?.includes(path)
    );

    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry || isExcluded) {
      return Promise.reject(error);
    }

    const { refreshToken } = getStoredTokens();
    if (!refreshToken) {
      clearStoredTokens();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve) => {
        pendingRequests.push((token: string) => {
          originalRequest.headers.set("Authorization", `Bearer ${token}`);
          resolve(apiClient(originalRequest));
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
      setStoredTokens(data.access_token, data.refresh_token);
      pendingRequests.forEach((resolvePending) => resolvePending(data.access_token));
      pendingRequests = [];

      originalRequest.headers.set("Authorization", `Bearer ${data.access_token}`);
      return apiClient(originalRequest);
    } catch (refreshError) {
      clearStoredTokens();
      pendingRequests = [];
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

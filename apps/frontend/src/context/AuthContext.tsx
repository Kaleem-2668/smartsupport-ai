"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { fetchCurrentUser, loginUser, registerUser, type User } from "@/lib/api/auth";
import { clearStoredTokens, getStoredTokens, setStoredTokens } from "@/lib/api/tokenStorage";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    async function loadCurrentUser() {
      const { accessToken } = getStoredTokens();
      if (!accessToken) {
        if (isMounted) setIsLoading(false);
        return;
      }
      try {
        const currentUser = await fetchCurrentUser();
        if (isMounted) setUser(currentUser);
      } catch {
        clearStoredTokens();
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadCurrentUser();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await loginUser(email, password);
      setStoredTokens(tokens.access_token, tokens.refresh_token);
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
      router.push("/dashboard");
    },
    [router]
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      await registerUser(email, password, fullName);
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(() => {
    clearStoredTokens();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

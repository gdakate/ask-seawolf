"use client";
import { useState, useEffect } from "react";
import { getToken, clearToken } from "@/lib/api";

interface AuthState {
  isLoggedIn: boolean;
  userId: string | null;
  name: string | null;
  email: string | null;
  loading: boolean;
}

export function useAuth(): AuthState & { logout: () => void } {
  const [state, setState] = useState<AuthState>({
    isLoggedIn: false, userId: null, name: null, email: null, loading: true,
  });

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setState({ isLoggedIn: false, userId: null, name: null, email: null, loading: false });
      return;
    }
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        clearToken();
        setState({ isLoggedIn: false, userId: null, name: null, email: null, loading: false });
        return;
      }
      setState({ isLoggedIn: true, userId: payload.sub ?? null, name: payload.name ?? null, email: payload.email ?? null, loading: false });
    } catch {
      clearToken();
      setState({ isLoggedIn: false, userId: null, name: null, email: null, loading: false });
    }
  }, []);

  return {
    ...state,
    logout: () => {
      clearToken();
      setState({ isLoggedIn: false, userId: null, name: null, email: null, loading: false });
    },
  };
}

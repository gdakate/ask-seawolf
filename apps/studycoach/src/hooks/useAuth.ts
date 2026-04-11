"use client";
import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
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
  const pathname = usePathname();

  const readToken = useCallback(() => {
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

  // Re-read token on every route change (catches post-login navigation)
  useEffect(() => {
    readToken();
  }, [pathname, readToken]);

  // Also listen for explicit auth change events (same-page updates)
  useEffect(() => {
    window.addEventListener("sc_auth_change", readToken);
    return () => window.removeEventListener("sc_auth_change", readToken);
  }, [readToken]);

  return {
    ...state,
    logout: () => {
      clearToken();
      setState({ isLoggedIn: false, userId: null, name: null, email: null, loading: false });
    },
  };
}

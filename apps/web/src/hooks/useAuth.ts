"use client";

import { useState, useEffect } from "react";
import { getPublicToken, clearPublicToken } from "@/lib/api";

interface AuthState {
  isLoggedIn: boolean;
  email: string | null;
  name: string | null;
  loading: boolean;
}

function parseToken(token: string): { email: string; name?: string } | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return { email: payload.email, name: payload.name };
  } catch {
    return null;
  }
}

export function useAuth(): AuthState & { logout: () => void } {
  const [state, setState] = useState<AuthState>({
    isLoggedIn: false,
    email: null,
    name: null,
    loading: true,
  });

  useEffect(() => {
    const token = getPublicToken();
    if (!token) {
      setState({ isLoggedIn: false, email: null, name: null, loading: false });
      return;
    }

    // Check expiry
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        clearPublicToken();
        setState({ isLoggedIn: false, email: null, name: null, loading: false });
        return;
      }
      setState({
        isLoggedIn: true,
        email: payload.email ?? null,
        name: payload.name ?? null,
        loading: false,
      });
    } catch {
      clearPublicToken();
      setState({ isLoggedIn: false, email: null, name: null, loading: false });
    }
  }, []);

  const logout = () => {
    clearPublicToken();
    setState({ isLoggedIn: false, email: null, name: null, loading: false });
  };

  return { ...state, logout };
}

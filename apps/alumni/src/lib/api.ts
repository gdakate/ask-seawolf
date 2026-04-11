const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("alumni_token");
}
export function setToken(t: string) {
  if (typeof window !== "undefined") localStorage.setItem("alumni_token", t);
}
export function clearToken() {
  if (typeof window !== "undefined") localStorage.removeItem("alumni_token");
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ─── Auth ─────────────────────────────────────────────────────────
export interface AuthResponse {
  access_token: string;
  user_id: string;
  name: string;
  email: string;
  has_profile: boolean;
}

export async function register(email: string, password: string, name: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/alumni/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/alumni/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

// ─── Profile ──────────────────────────────────────────────────────
export interface Profile {
  id: string;
  user_id: string;
  name: string;
  email: string;
  major: string;
  degree: string;
  graduation_year: number;
  is_international: boolean;
  current_company?: string;
  job_title?: string;
  industry?: string;
  location?: string;
  skills: string[];
  interests: string[];
  open_to: string[];
  linkedin_url?: string;
  bio?: string;
  is_visible: boolean;
  created_at: string;
}

export const getMyProfile = () => apiFetch<Profile>("/api/alumni/profile/me");
export const getProfile = (id: string) => apiFetch<Profile>(`/api/alumni/profile/${id}`);
export const createProfile = (data: any) =>
  apiFetch<Profile>("/api/alumni/profile", { method: "POST", body: JSON.stringify(data) });
export const updateProfile = (data: any) =>
  apiFetch<Profile>("/api/alumni/profile/me", { method: "PUT", body: JSON.stringify(data) });

// ─── Matches ──────────────────────────────────────────────────────
export interface Match {
  profile: Profile;
  match_score: number;
  match_pct: string;
  reasons: string[];
}

export const getMatches = () => apiFetch<Match[]>("/api/alumni/matches");

// ─── Feed ─────────────────────────────────────────────────────────
export interface Post {
  id: string;
  content: string;
  tags: string[];
  likes_count: number;
  comments_count: number;
  is_pinned: boolean;
  created_at: string;
  author: {
    id: string;
    name: string;
    job_title?: string;
    current_company?: string;
    major: string;
    graduation_year: number;
  };
}

export interface Comment {
  id: string;
  content: string;
  created_at: string;
  author: { name: string; job_title?: string; id: string };
}

export const getFeed = (page = 1) => apiFetch<Post[]>(`/api/alumni/feed?page=${page}`);
export const createPost = (content: string, tags: string[]) =>
  apiFetch("/api/alumni/feed", { method: "POST", body: JSON.stringify({ content, tags }) });
export const deletePost = (id: string) =>
  apiFetch(`/api/alumni/feed/${id}`, { method: "DELETE" });
export const getComments = (postId: string) =>
  apiFetch<Comment[]>(`/api/alumni/feed/${postId}/comments`);
export const addComment = (postId: string, content: string) =>
  apiFetch(`/api/alumni/feed/${postId}/comments`, { method: "POST", body: JSON.stringify({ content }) });
export const toggleLike = (postId: string) =>
  apiFetch<{ liked: boolean; likes_count: number }>(`/api/alumni/feed/${postId}/like`, { method: "POST" });

// ─── Connections ──────────────────────────────────────────────────
export const toggleConnect = (targetUserId: string) =>
  apiFetch<{ connected: boolean }>(`/api/alumni/connect/${targetUserId}`, { method: "POST" });
export const getConnections = () => apiFetch<Profile[]>("/api/alumni/connections");
export const getConnectionIds = () => apiFetch<{ ids: string[] }>("/api/alumni/connections/ids");

// ─── Resume ───────────────────────────────────────────────────────
export async function parseResume(file: File): Promise<{ extracted: Partial<Profile>; raw_text_preview: string }> {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/alumni/resume/parse`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) throw new Error("Resume parse failed");
  return res.json();
}

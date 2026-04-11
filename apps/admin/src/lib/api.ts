const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let token: string | null = null;

export function setToken(t: string) {
  token = t;
  if (typeof window !== "undefined") localStorage.setItem("admin_token", t);
}

export function getToken(): string | null {
  if (token) return token;
  if (typeof window !== "undefined") return localStorage.getItem("admin_token");
  return null;
}

export function clearToken() {
  token = null;
  if (typeof window !== "undefined") localStorage.removeItem("admin_token");
}

async function adminFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const t = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(t ? { Authorization: `Bearer ${t}` } : {}),
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

// Auth
export async function login(email: string, password: string) {
  const data = await adminFetch<{ access_token: string; email: string; role: string }>(
    "/api/admin/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
  setToken(data.access_token);
  return data;
}

export async function register(email: string, password: string, name: string) {
  const data = await adminFetch<{ access_token: string; email: string; role: string }>(
    "/api/admin/auth/register",
    { method: "POST", body: JSON.stringify({ email, password, name }) }
  );
  setToken(data.access_token);
  return data;
}

// Dashboard
export const getDashboard = () => adminFetch<any>("/api/admin/dashboard");

// Sources
export const getSources = () => adminFetch<any[]>("/api/admin/sources");
export const createSource = (data: any) => adminFetch("/api/admin/sources", { method: "POST", body: JSON.stringify(data) });
export const updateSource = (id: string, data: any) => adminFetch(`/api/admin/sources/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteSource = (id: string) => adminFetch(`/api/admin/sources/${id}`, { method: "DELETE" });

// Documents
export const getDocuments = (params?: string) => adminFetch<any[]>(`/api/admin/documents${params ? `?${params}` : ""}`);
export const getDocument = (id: string) => adminFetch<any>(`/api/admin/documents/${id}`);

// Chunks
export const getChunks = (params?: string) => adminFetch<any[]>(`/api/admin/chunks${params ? `?${params}` : ""}`);

// Jobs
export const triggerCrawl = (sourceId?: string) => adminFetch("/api/admin/crawl" + (sourceId ? `?source_id=${sourceId}` : ""), { method: "POST" });
export const triggerReindex = () => adminFetch("/api/admin/reindex", { method: "POST" });

// Conversations
export const getConversations = () => adminFetch<any[]>("/api/admin/conversations");
export const getConversationMessages = (id: string) => adminFetch<any[]>(`/api/admin/conversations/${id}/messages`);

// Feedback
export const getFeedback = () => adminFetch<any[]>("/api/admin/feedback");

// FAQs
export const getFaqs = () => adminFetch<any[]>("/api/admin/faqs");
export const createFaq = (data: any) => adminFetch("/api/admin/faqs", { method: "POST", body: JSON.stringify(data) });
export const updateFaq = (id: string, data: any) => adminFetch(`/api/admin/faqs/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteFaq = (id: string) => adminFetch(`/api/admin/faqs/${id}`, { method: "DELETE" });

// Analytics
export const getAnalytics = () => adminFetch<any>("/api/admin/analytics");
export const getFaqSuggestions = () => adminFetch<any[]>("/api/admin/faq-suggestions");

// Evaluations
export const getEvaluations = () => adminFetch<any[]>("/api/admin/evaluations");
export const getEvaluationCases = (runId: string) => adminFetch<any[]>(`/api/admin/evaluations/${runId}/cases`);
export const runEvaluation = (name?: string) => adminFetch("/api/admin/evaluations/run" + (name ? `?name=${name}` : ""), { method: "POST" });

// Settings
export const getAdminSettings = () => adminFetch<any>("/api/admin/settings");

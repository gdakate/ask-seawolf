const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Citation {
  title: string;
  url: string;
  snippet: string;
  office?: string;
  category?: string;
}

export interface OfficeRouting {
  name: string;
  office_key: string;
  phone?: string;
  email?: string;
  url?: string;
  reason: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  office_routing?: OfficeRouting;
  follow_up_questions: string[];
  confidence_score: number;
  session_id: string;
  warning?: string;
}

export interface Topic {
  key: string;
  name: string;
  description: string;
  icon?: string;
}

export interface Office {
  id: string;
  name: string;
  office_key: string;
  description?: string;
  phone?: string;
  email?: string;
  url?: string;
  location?: string;
  hours?: string;
  category: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export async function sendChatQuery(
  query: string,
  sessionId?: string
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/api/chat/query", {
    method: "POST",
    body: JSON.stringify({ query, session_id: sessionId }),
  });
}

export async function getTopics(): Promise<Topic[]> {
  return apiFetch<Topic[]>("/api/topics");
}

export async function getOffices(): Promise<Office[]> {
  return apiFetch<Office[]>("/api/offices");
}

export async function submitFeedback(data: {
  message_id?: string;
  rating?: number;
  comment?: string;
  feedback_type?: string;
}): Promise<void> {
  await apiFetch("/api/feedback", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function searchDocuments(
  q: string,
  category?: string
): Promise<{ items: any[]; total: number }> {
  const params = new URLSearchParams({ q });
  if (category) params.set("category", category);
  return apiFetch(`/api/search?${params}`);
}

export async function getHealth(): Promise<{ status: string }> {
  return apiFetch("/api/health");
}

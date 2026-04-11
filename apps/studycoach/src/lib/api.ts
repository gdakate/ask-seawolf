const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sc_token");
}
export function setToken(t: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("sc_token", t);
    window.dispatchEvent(new Event("sc_auth_change"));
  }
}
export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("sc_token");
    window.dispatchEvent(new Event("sc_auth_change"));
  }
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

// ─── Auth ──────────────────────────────────────────────────────────
export interface AuthResponse {
  access_token: string;
  user_id: string;
  name: string;
  email: string;
}

export async function register(email: string, password: string, name: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/study/auth/register", {
    method: "POST", body: JSON.stringify({ email, password, name }),
  });
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/study/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

// ─── Courses ───────────────────────────────────────────────────────
export interface Course {
  id: string;
  code: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Section {
  id: string;
  material_id: string;
  material_filename: string;
  title: string;
  order: number;
  difficulty: number;
  concepts: string[];
  prerequisites: string[];
}

export interface Material {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  parsed_at?: string;
  created_at: string;
}

export interface CourseDetail extends Course {
  materials: Material[];
  sections: Section[];
  sections_by_material: Record<string, Section[]>;
}

export const getCourses = () => apiFetch<Course[]>("/api/study/courses");
export const getCourse = (id: string) => apiFetch<CourseDetail>(`/api/study/courses/${id}`);
export const createCourse = (data: { code: string; name: string; description?: string }) =>
  apiFetch<Course>("/api/study/courses", { method: "POST", body: JSON.stringify(data) });
export const deleteCourse = (id: string) =>
  apiFetch(`/api/study/courses/${id}`, { method: "DELETE" });

export async function uploadMaterial(courseId: string, file: File): Promise<Material> {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/study/courses/${courseId}/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export const deleteMaterial = (courseId: string, materialId: string) =>
  apiFetch(`/api/study/courses/${courseId}/materials/${materialId}`, { method: "DELETE" });

// ─── Study Plan ────────────────────────────────────────────────────
export interface PlanItem {
  id: string;
  course_id: string;
  title: string;
  due_date?: string;
  item_type: string;
  is_completed: boolean;
  notes?: string;
  created_at: string;
}

export const getPlan = (courseId: string) => apiFetch<PlanItem[]>(`/api/study/courses/${courseId}/plan`);
export const addPlanItem = (courseId: string, data: Partial<PlanItem>) =>
  apiFetch<PlanItem>(`/api/study/courses/${courseId}/plan`, { method: "POST", body: JSON.stringify(data) });
export const updatePlanItem = (itemId: string, data: Partial<PlanItem>) =>
  apiFetch<PlanItem>(`/api/study/plan/${itemId}`, { method: "PUT", body: JSON.stringify(data) });
export const deletePlanItem = (itemId: string) =>
  apiFetch(`/api/study/plan/${itemId}`, { method: "DELETE" });
export const generatePlan = (courseId: string) =>
  apiFetch<PlanItem[]>(`/api/study/courses/${courseId}/plan/generate`, { method: "POST" });

// ─── Teaching ──────────────────────────────────────────────────────
export interface TeachMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface TeachSession {
  id: string;
  knowledge_level: string;
  section_id: string | null;
  section_title: string | null;
  message_count: number;
  preview: string;
  created_at: string;
}

export const sendTeachMessage = (data: {
  course_id: string;
  message: string;
  session_id?: string;
  section_id?: string;
  knowledge_level?: string;
}) => apiFetch<{ response: string; session_id: string }>("/api/study/teach", {
  method: "POST", body: JSON.stringify(data),
});

export interface TeachSessionWithCourse extends TeachSession {
  course_id: string;
  course_name: string;
  course_code: string;
}

export const getSessions = (courseId: string) =>
  apiFetch<TeachSession[]>(`/api/study/courses/${courseId}/sessions`);

export const getAllSessions = () =>
  apiFetch<TeachSessionWithCourse[]>(`/api/study/sessions`);

export const deleteSection = (sectionId: string) =>
  apiFetch(`/api/study/sections/${sectionId}`, { method: "DELETE" });

export const getSessionMessages = (sessionId: string) =>
  apiFetch<TeachMessage[]>(`/api/study/teach/${sessionId}/messages`);

export const deleteSession = (sessionId: string) =>
  apiFetch(`/api/study/sessions/${sessionId}`, { method: "DELETE" });

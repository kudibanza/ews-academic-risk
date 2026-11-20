import type { RiskCard, SCSQuestion, StudentSummary } from "./types";

const TOKEN_KEY = "ews_token";


export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export interface StudentPage {
  items: StudentSummary[];
  total: number;
  limit: number;
  offset: number;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    if (res.status === 401) clearToken();
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username, password });
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = (await res.json()) as { access_token: string };
  setToken(data.access_token);
  return data.access_token;
}

export const api = {
  windows: () => request<string[]>("/api/windows"),
  students: (window: string, flagged = true, limit = 50, offset = 0, studentId?: number | null) => {
    const params = new URLSearchParams({
      flagged: String(flagged),
      limit: String(limit),
      offset: String(offset),
    });
    if (studentId != null) params.set("student_id", String(studentId));
    return request<StudentPage>(`/api/students/${window}?${params.toString()}`);
  },
  riskCard: (studentId: number, window: string) =>
    request<RiskCard>(`/api/students/${studentId}/${window}`),
  scsQuestions: () => request<SCSQuestion[]>("/api/scs/questions"),
  scsSubmit: (responses: { id: number; score: number }[]) =>
    request<{ status: string }>("/api/scs/responses", {
      method: "POST",
      body: JSON.stringify({ responses }),
    }),
    admin: {
      users: () => request<import("./types").AdminUser[]>("/api/admin/users"),
      createUser: (username: string, password: string, role: "admin" | "advisor") =>
        request<import("./types").AdminUser>("/api/admin/users", {
          method: "POST",
          body: JSON.stringify({ username, password, role }),
        }),
      updateUser: (id: number, patch: { role?: "admin" | "advisor"; active?: boolean; password?: string }) =>
        request<import("./types").AdminUser>(`/api/admin/users/${id}`, {
          method: "PATCH",
          body: JSON.stringify(patch),
        }),
      deactivateUser: (id: number) =>
        request<import("./types").AdminUser>(`/api/admin/users/${id}`, {
          method: "DELETE",
        }),
      stats: (window: string) =>
        request<import("./types").WindowStats>(`/api/admin/stats/${window}`),
    },
};
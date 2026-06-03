export type User = {
  id: number;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type StudySetting = {
  id: number;
  user_id: number;
  daily_available_hours: number;
};

export type Subject = {
  id: number;
  user_id: number;
  name: string;
  deadline_date: string;
  required_hours: number;
  completed_hours: number;
  status: "active" | "completed" | "archived";
  created_at: string;
  updated_at: string;
};

export type StudyPlan = {
  id: number;
  user_id: number;
  subject_id: number;
  plan_date: string;
  planned_hours: number;
  status: string;
  subject: Subject;
};

export type PlanSummary = {
  plan_date: string;
  daily_available_hours: number;
  total_planned_hours: number;
  over_capacity: boolean;
  plans: StudyPlan[];
};

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");

function apiUrl(path: string): string {
  return `${API_BASE_URL}/${path.replace(/^\/+/, "")}`;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("schedule-token");
}

export function setToken(token: string): void {
  window.localStorage.setItem("schedule-token", token);
}

export function clearToken(): void {
  window.localStorage.removeItem("schedule-token");
}

type ApiOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
};

function errorMessageFromDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String(item.msg);
        }
        return JSON.stringify(item);
      })
      .join(", ");
  }
  if (detail && typeof detail === "object" && "msg" in detail) {
    return String(detail.msg);
  }
  return null;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(apiUrl(path), {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 401 && typeof window !== "undefined") {
    clearToken();
    window.location.href = "/login";
  }

  if (!response.ok) {
    let message = "API request failed";
    try {
      const data = (await response.json()) as { detail?: unknown };
      message = errorMessageFromDetail(data.detail) ?? message;
    } catch {
      message = response.statusText;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function formatHours(value: number): string {
  const totalMinutes = Math.max(0, Math.round(value * 60));
  if (value > 0 && totalMinutes === 0) return "1分未満";

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) return `${minutes}分`;
  if (minutes === 0) return `${hours}時間`;
  return `${hours}時間${minutes}分`;
}

export function progressPercent(subject: Subject): number {
  if (subject.required_hours <= 0) return 0;
  return Math.min(100, Math.round((subject.completed_hours / subject.required_hours) * 100));
}

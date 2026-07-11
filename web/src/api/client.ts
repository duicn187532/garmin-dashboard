import type {
  ActivityDetail,
  ActivityLap,
  ActivityListResponse,
  ActivityTrackpoint,
  AiReport,
  DashboardTrendsResponse,
  DailyHealth,
  TodayResponse
} from "../types/api";

const API_BASE_KEY = "garminInsight.apiBaseUrl";
const SYNC_TOKEN_KEY = "garminInsight.syncToken";
const APP_TOKEN_KEY = "garminInsight.appAccessToken";

export function getApiBaseUrl(): string {
  return localStorage.getItem(API_BASE_KEY) || import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
}

export function setApiBaseUrl(value: string) {
  localStorage.setItem(API_BASE_KEY, value.replace(/\/$/, ""));
}

export function getSyncToken(): string {
  return localStorage.getItem(SYNC_TOKEN_KEY) || "";
}

export function setSyncToken(value: string) {
  localStorage.setItem(SYNC_TOKEN_KEY, value);
}

export function getAppAccessToken(): string {
  return localStorage.getItem(APP_TOKEN_KEY) || "";
}

export function setAppAccessToken(value: string) {
  localStorage.setItem(APP_TOKEN_KEY, value);
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, apiBaseUrl = getApiBaseUrl()): Promise<T> {
  const { headers, ...restOptions } = options;
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...restOptions,
    headers: {
      "Content-Type": "application/json",
      ...(getAppAccessToken() ? { "X-App-Token": getAppAccessToken() } : {}),
      ...(headers || {})
    }
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  status: (baseUrl?: string) => apiFetch<{ status: string }>("/api/status", {}, baseUrl),
  summary: (baseUrl?: string) =>
    apiFetch<{
      activities: number;
      daily_health_days: number;
      ai_reports: number;
      latest_health_date: string | null;
      latest_activity_time: string | null;
    }>("/api/summary", {}, baseUrl),
  today: (baseUrl?: string) => apiFetch<TodayResponse>("/api/dashboard/today", {}, baseUrl),
  trends: (range: string, baseUrl?: string) =>
    apiFetch<DashboardTrendsResponse>(`/api/dashboard/trends?range=${range}`, {}, baseUrl),
  activities: (query: URLSearchParams, baseUrl?: string) =>
    apiFetch<ActivityListResponse>(`/api/activities?${query.toString()}`, {}, baseUrl),
  activityDetail: (activityId: string, baseUrl?: string) =>
    apiFetch<ActivityDetail>(`/api/activities/${encodeURIComponent(activityId)}`, {}, baseUrl),
  activityLaps: (activityId: string, baseUrl?: string) =>
    apiFetch<ActivityLap[]>(`/api/activities/${encodeURIComponent(activityId)}/laps`, {}, baseUrl),
  activityTrackpoints: (activityId: string, baseUrl?: string) =>
    apiFetch<ActivityTrackpoint[]>(`/api/activities/${encodeURIComponent(activityId)}/trackpoints`, {}, baseUrl),
  healthDaily: (baseUrl?: string) => apiFetch<DailyHealth[]>("/api/health/daily", {}, baseUrl),
  healthTrend: (metric: string, range: string, baseUrl?: string) =>
    apiFetch<{ metric: string; range: string; points: { date: string; value: number | null }[] }>(
      `/api/health/trends?metric=${metric}&range=${range}`,
      {},
      baseUrl
    ),
  sync: (days: number, token: string, baseUrl?: string) =>
    apiFetch<{ status: string; source: string; message?: string }>(
      "/api/sync/garmin",
      {
        method: "POST",
        headers: token ? { "X-Sync-Token": token } : {},
        body: JSON.stringify({ days })
      },
      baseUrl
    ),
  analyze: (baseUrl?: string) =>
    apiFetch<AiReport>("/api/ai/analyze", {
      method: "POST",
      body: JSON.stringify({ report_type: "today" })
    }, baseUrl),
  ask: (question: string, baseUrl?: string) =>
    apiFetch<AiReport>("/api/ai/query", {
      method: "POST",
      body: JSON.stringify({ question })
    }, baseUrl),
  latestAi: (baseUrl?: string) => apiFetch<AiReport | null>("/api/ai/latest", {}, baseUrl),
  reports: (baseUrl?: string) => apiFetch<AiReport[]>("/api/ai/reports", {}, baseUrl)
};

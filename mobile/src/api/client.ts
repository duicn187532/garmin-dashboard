import AsyncStorage from "@react-native-async-storage/async-storage";
import type { ActivityListResponse, AiReport, DashboardTrendsResponse, TodayResponse } from "../types/api";

const API_BASE_KEY = "garminInsight.apiBaseUrl";
const SYNC_TOKEN_KEY = "garminInsight.syncToken";
const APP_TOKEN_KEY = "garminInsight.appAccessToken";

export async function getApiBaseUrl() {
  return (await AsyncStorage.getItem(API_BASE_KEY)) || "http://127.0.0.1:8000";
}

export async function setApiBaseUrl(value: string) {
  await AsyncStorage.setItem(API_BASE_KEY, value.replace(/\/$/, ""));
}

export async function getSyncToken() {
  return (await AsyncStorage.getItem(SYNC_TOKEN_KEY)) || "";
}

export async function setSyncToken(value: string) {
  await AsyncStorage.setItem(SYNC_TOKEN_KEY, value);
}

export async function getAppAccessToken() {
  return (await AsyncStorage.getItem(APP_TOKEN_KEY)) || "";
}

export async function setAppAccessToken(value: string) {
  await AsyncStorage.setItem(APP_TOKEN_KEY, value);
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = await getApiBaseUrl();
  const appToken = await getAppAccessToken();
  const { headers, ...restOptions } = options;
  const response = await fetch(`${baseUrl}${path}`, {
    ...restOptions,
    headers: { "Content-Type": "application/json", ...(appToken ? { "X-App-Token": appToken } : {}), ...(headers || {}) }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as T;
}

export const api = {
  status: async () => apiFetch<{ status: string }>("/api/status"),
  today: async () => apiFetch<TodayResponse>("/api/dashboard/today"),
  trends: async (range: string) => apiFetch<DashboardTrendsResponse>(`/api/dashboard/trends?range=${range}`),
  activities: async () => apiFetch<ActivityListResponse>("/api/activities?page=1&page_size=30&sort=start_time_desc"),
  sync: async (days: number) => {
    const token = await getSyncToken();
    return apiFetch<{ status: string }>("/api/sync/garmin", {
      method: "POST",
      headers: token ? { "X-Sync-Token": token } : {},
      body: JSON.stringify({ days })
    });
  },
  analyze: async () =>
    apiFetch<AiReport>("/api/ai/analyze", {
      method: "POST",
      body: JSON.stringify({ report_type: "today" })
    }),
  ask: async (question: string) =>
    apiFetch<AiReport>("/api/ai/query", {
      method: "POST",
      body: JSON.stringify({ question })
    }),
  latestAi: async () => apiFetch<AiReport | null>("/api/ai/latest")
};

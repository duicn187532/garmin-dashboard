import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, getSyncToken } from "../api/client";
import type { ActivityListResponse, AiReport, DashboardTrendsResponse, TodayResponse } from "../types/api";

type Summary = {
  activities: number;
  daily_health_days: number;
  ai_reports: number;
  latest_health_date: string | null;
  latest_activity_time: string | null;
};

type ClientCache = {
  savedAt: string;
  summary: Summary | null;
  today: TodayResponse | null;
  trendsByRange: Record<string, DashboardTrendsResponse | undefined>;
  activities: ActivityListResponse | null;
  latestAi: AiReport | null;
};

type AppDataContextValue = {
  apiBaseUrl: string;
  range: string;
  setRange: (range: string) => void;
  cache: ClientCache;
  loading: boolean;
  syncing: boolean;
  error: string | null;
  refreshFromBackend: (options?: { sync?: boolean; days?: number }) => Promise<void>;
  runAnalyze: () => Promise<void>;
  askAi: (question: string) => Promise<AiReport>;
  clearCache: () => void;
};

const emptyCache: ClientCache = {
  savedAt: "",
  summary: null,
  today: null,
  trendsByRange: {},
  activities: null,
  latestAi: null
};

const HEALTH_FRESH_WINDOW_DAYS = 2;
const AUTO_SYNC_COOLDOWN_MS = 12 * 60 * 60 * 1000;

const AppDataContext = createContext<AppDataContextValue | null>(null);

export function AppDataProvider({ apiBaseUrl, children }: { apiBaseUrl: string; children: ReactNode }) {
  const [range, setRange] = useState("30d");
  const [cache, setCache] = useState<ClientCache>(() => loadCache(apiBaseUrl));
  const [loading, setLoading] = useState(!loadCache(apiBaseUrl).today);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveCache = useCallback(
    (next: ClientCache) => {
      setCache(next);
      saveCacheToStorage(apiBaseUrl, next);
    },
    [apiBaseUrl]
  );

  const refreshFromBackend = useCallback(
    async (options: { sync?: boolean; days?: number } = {}) => {
      setError(null);
      setSyncing(Boolean(options.sync));
      setLoading((current) => current || !cache.today);
      try {
        if (options.sync) {
          await api.sync(options.days || 30, getSyncToken(), apiBaseUrl);
        }
        const [summary, today, trends7, trends30, trends90, activities, latestAi] = await Promise.all([
          api.summary(apiBaseUrl),
          api.today(apiBaseUrl),
          api.trends("7d", apiBaseUrl),
          api.trends("30d", apiBaseUrl),
          api.trends("90d", apiBaseUrl),
          api.activities(new URLSearchParams({ page: "1", page_size: "200", sort: "start_time_desc" }), apiBaseUrl),
          api.latestAi(apiBaseUrl)
        ]);
        saveCache({
          savedAt: new Date().toISOString(),
          summary,
          today,
          activities,
          latestAi,
          trendsByRange: { "7d": trends7, "30d": trends30, "90d": trends90 }
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
        setSyncing(false);
      }
    },
    [apiBaseUrl, cache.today, saveCache]
  );

  useEffect(() => {
    let cancelled = false;
    const cached = loadCache(apiBaseUrl);
    setCache(cached);
    setLoading(!cached.today);
    setError(null);

    async function bootstrap() {
      try {
        const summary = await api.summary(apiBaseUrl);
        if (cancelled) return;
        if (shouldAutoSync(summary.latest_health_date, apiBaseUrl)) {
          markAutoSyncAttempt(apiBaseUrl);
          await refreshFromBackend({ sync: true, days: 30 });
          return;
        }
        if (!isCompleteCacheForSummary(cached, summary)) {
          await refreshFromBackend({ sync: false });
          return;
        }
        saveCache({ ...cached, summary, savedAt: cached.savedAt || new Date().toISOString() });
        setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

  const runAnalyze = useCallback(async () => {
    setError(null);
    try {
      const report = await api.analyze(apiBaseUrl);
      const next = { ...cache, latestAi: report, today: cache.today ? { ...cache.today, ai_report: report } : cache.today };
      saveCache(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [apiBaseUrl, cache, saveCache]);

  const askAi = useCallback(
    async (question: string) => {
      const report = await api.ask(question, apiBaseUrl);
      const next = { ...cache, latestAi: report };
      saveCache(next);
      return report;
    },
    [apiBaseUrl, cache, saveCache]
  );

  const clearCache = useCallback(() => {
    localStorage.removeItem(cacheKey(apiBaseUrl));
    localStorage.removeItem(autoSyncKey(apiBaseUrl));
    setCache(emptyCache);
  }, [apiBaseUrl]);

  const value = useMemo(
    () => ({ apiBaseUrl, range, setRange, cache, loading, syncing, error, refreshFromBackend, runAnalyze, askAi, clearCache }),
    [apiBaseUrl, range, cache, loading, syncing, error, refreshFromBackend, runAnalyze, askAi, clearCache]
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const value = useContext(AppDataContext);
  if (!value) throw new Error("useAppData must be used within AppDataProvider.");
  return value;
}

function cacheKey(apiBaseUrl: string) {
  return `garminInsight.clientCache.${apiBaseUrl}`;
}

function loadCache(apiBaseUrl: string): ClientCache {
  const raw = localStorage.getItem(cacheKey(apiBaseUrl));
  if (!raw) return emptyCache;
  try {
    return { ...emptyCache, ...JSON.parse(raw) };
  } catch {
    return emptyCache;
  }
}

function isCompleteCacheForSummary(cache: ClientCache, summary: Summary) {
  const latestHealthDate = summary.latest_health_date;
  if (!cache.today || !cache.summary || !cache.activities) return false;
  if (!cache.trendsByRange["7d"] || !cache.trendsByRange["30d"] || !cache.trendsByRange["90d"]) return false;
  if (cache.summary.latest_health_date !== latestHealthDate) return false;
  if (cache.today.health?.date !== latestHealthDate) return false;
  return true;
}

function saveCacheToStorage(apiBaseUrl: string, cache: ClientCache) {
  const key = cacheKey(apiBaseUrl);
  const compact = compactCacheForStorage(cache);
  try {
    localStorage.removeItem(key);
    localStorage.setItem(key, JSON.stringify(compact));
  } catch {
    const minimal: ClientCache = {
      ...emptyCache,
      savedAt: compact.savedAt,
      summary: compact.summary,
      today: compact.today
        ? {
            ...compact.today,
            ai_report: compact.today.ai_report ? compactAiReport(compact.today.ai_report) : null,
            recent_activities: compact.today.recent_activities.slice(0, 5)
          }
        : null,
      trendsByRange: {
        "7d": compact.trendsByRange["7d"]
      }
    };
    try {
      localStorage.removeItem(key);
      localStorage.setItem(key, JSON.stringify(minimal));
    } catch {
      localStorage.removeItem(key);
    }
  }
}

function compactCacheForStorage(cache: ClientCache): ClientCache {
  return {
    ...cache,
    latestAi: cache.latestAi ? compactAiReport(cache.latestAi) : null,
    today: cache.today
      ? {
          ...cache.today,
          ai_report: cache.today.ai_report ? compactAiReport(cache.today.ai_report) : null
        }
      : null
  };
}

function compactAiReport(report: AiReport): AiReport {
  return {
    ...report,
    evidence_json: summarizeEvidence(report.evidence_json)
  };
}

function summarizeEvidence(evidence: Record<string, unknown>): Record<string, unknown> {
  const dailyHealth = Array.isArray(evidence.daily_health) ? evidence.daily_health : [];
  const derivedMetrics = Array.isArray(evidence.derived_metrics) ? evidence.derived_metrics : [];
  const activities = Array.isArray(evidence.activities) ? evidence.activities : [];
  return {
    has_data: evidence.has_data,
    range: evidence.range,
    latest_health: compactRecord(evidence.latest_health),
    latest_metric: compactRecord(evidence.latest_metric),
    counts: {
      daily_health: dailyHealth.length,
      derived_metrics: derivedMetrics.length,
      activities: activities.length
    }
  };
}

function compactRecord(value: unknown): unknown {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  const { raw_json, evidence_json, ...rest } = value as Record<string, unknown>;
  return rest;
}

function localDate(offsetDays = 0) {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isRecentHealthDate(value: string | null) {
  if (!value) return false;
  const healthDate = value.slice(0, 10);
  return healthDate >= localDate(-HEALTH_FRESH_WINDOW_DAYS);
}

function shouldAutoSync(latestHealthDate: string | null, apiBaseUrl: string) {
  if (isRecentHealthDate(latestHealthDate)) return false;
  const lastAttempt = readLastAutoSyncAttempt(apiBaseUrl);
  if (Number.isFinite(lastAttempt) && Date.now() - lastAttempt < AUTO_SYNC_COOLDOWN_MS) return false;
  return true;
}

function readLastAutoSyncAttempt(apiBaseUrl: string) {
  try {
    return Number(localStorage.getItem(autoSyncKey(apiBaseUrl)) || "0");
  } catch {
    return 0;
  }
}

function markAutoSyncAttempt(apiBaseUrl: string) {
  try {
    localStorage.setItem(autoSyncKey(apiBaseUrl), String(Date.now()));
  } catch {
    // Ignore storage failures; auto sync should never block app bootstrap.
  }
}

function autoSyncKey(apiBaseUrl: string) {
  return `garminInsight.lastAutoSyncAt.${apiBaseUrl}`;
}

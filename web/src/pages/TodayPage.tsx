import { Bot, RefreshCcw, RotateCw, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";
import { LoadChart } from "../charts/LoadChart";
import { MetricLineChart } from "../charts/MetricLineChart";
import { EmptyState } from "../components/EmptyState";
import { EnergyGauge } from "../components/EnergyGauge";
import { LoadingBlock } from "../components/LoadingBlock";
import { RangeTabs } from "../components/RangeTabs";
import { StatCard } from "../components/StatCard";
import { useAppData } from "../state/AppDataContext";
import type { DashboardTrendsResponse, DailyHealth } from "../types/api";
import { fmtDistance, fmtNumber, riskTone } from "../utils/format";

type Props = {
  apiBaseUrl: string;
};

export function TodayPage({ apiBaseUrl }: Props) {
  const { cache, range, setRange, loading, error, syncing, refreshFromBackend, runAnalyze: analyzeFromCache } = useAppData();
  const data = cache.today && cache.trendsByRange[range] ? { today: cache.today, trends: cache.trendsByRange[range]! } : null;
  const [busy, setBusy] = useState<string | null>(null);

  async function runSync() {
    setBusy("sync");
    try {
      await refreshFromBackend({ sync: true, days: range === "90d" ? 90 : range === "7d" ? 7 : 30 });
    } finally {
      setBusy(null);
    }
  }

  async function runAiAnalysis() {
    setBusy("ai");
    try {
      await analyzeFromCache();
    } finally {
      setBusy(null);
    }
  }

  const period = useMemo(() => (data ? buildPeriodSummary(data.trends) : null), [data]);

  if (loading || syncing) return <LoadingBlock />;
  if (error) return <EmptyState title="Backend unavailable" message={error} />;
  if (!data?.today.health) {
    return (
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-pine">Today</p>
            <h2 className="text-3xl font-semibold">No Garmin data yet</h2>
          </div>
          <button className="rounded-xl bg-pine px-4 py-2 text-sm font-semibold text-surface" onClick={runSync}>
            Sync data
          </button>
        </div>
        <EmptyState title="Empty dashboard" message="Run sync to load Garmin data, then this page becomes your daily monitoring console." />
      </section>
    );
  }

  const health = data.today.health;
  const metric = data.today.derived_metric;
  const bodyBattery = avgDefined([health.body_battery_min, health.body_battery_max]);
  const stressReadiness = health.stress_avg === null || health.stress_avg === undefined ? null : Math.max(0, 100 - health.stress_avg);
  const sleepScore = health.sleep_hours === null || health.sleep_hours === undefined ? null : Math.min(100, (health.sleep_hours / 8) * 100);
  const loadMax = Math.max(100, (metric?.chronic_load_28d || 60) * 1.8, (metric?.acute_load_7d || 60) * 1.3);

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-line bg-panel/70 p-4 shadow-soft backdrop-blur sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-pine">Monitoring window</p>
            <h2 className="mt-1 text-3xl font-semibold sm:text-4xl">Recovery and load control</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              {health.date} baseline with {range} trend context. Values are grounded in your local database.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <RangeTabs value={range} onChange={setRange} />
            <button
              className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-panel2 px-3 text-sm font-semibold text-ink"
              disabled={busy !== null}
              onClick={runSync}
              type="button"
            >
              <RefreshCcw size={16} /> {busy === "sync" ? "Syncing" : "Sync"}
            </button>
            <button
              className="inline-flex h-10 items-center gap-2 rounded-xl bg-pine px-3 text-sm font-semibold text-surface"
              disabled={busy !== null}
              onClick={runAiAnalysis}
              type="button"
            >
              <Bot size={16} /> {busy === "ai" ? "Analyzing" : "AI"}
            </button>
            <button className="rounded-xl border border-line bg-panel2 p-2" onClick={() => refreshFromBackend({ sync: false })} title="Reload cache" type="button">
              <RotateCw size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <EnergyGauge label="Recovery" value={metric?.recovery_score} helper={metric?.risk_level || "risk"} tone="pine" />
          <EnergyGauge label="ACWR" value={metric?.acwr} max={2} helper="7d / 28d" tone="amber" />
          <EnergyGauge label="Load" value={metric?.acute_load_7d} max={loadMax} helper="7d avg" tone="coral" />
          <EnergyGauge label="Body Battery" value={bodyBattery} helper="daily avg" tone="teal" />
        </div>

        <div className={`rounded-2xl border p-4 shadow-soft ${riskTone(metric?.risk_level)}`}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">AI Coach</p>
              <h3 className="mt-1 text-xl font-semibold text-ink">Today recommendation</h3>
            </div>
            <Bot size={22} className="text-pine" />
          </div>
          <p className="mt-3 max-h-56 overflow-auto whitespace-pre-line text-sm leading-6 text-ink">
            {data.today.ai_report?.answer || "Run AI analysis after syncing data."}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        <StatCard label="Sleep" value={fmtNumber(health.sleep_hours, "h", 1)} sub={`score ${fmtNumber(sleepScore, "", 0)}`} tone="pine" />
        <StatCard label="HRV" value={fmtNumber(health.hrv_avg, " ms", 0)} sub={`${range} avg ${fmtNumber(period?.hrvAvg, "", 0)}`} tone="teal" />
        <StatCard label="RHR" value={fmtNumber(health.resting_hr, " bpm", 0)} sub={`${range} avg ${fmtNumber(period?.rhrAvg, "", 0)}`} tone="amber" />
        <StatCard label="Stress" value={fmtNumber(health.stress_avg, "", 0)} sub={`readiness ${fmtNumber(stressReadiness, "", 0)}`} tone="coral" />
        <StatCard label="Steps" value={fmtNumber(health.steps, "", 0)} sub={`${range} avg ${fmtNumber(period?.stepsAvg, "", 0)}`} tone="pine" />
        <StatCard label="Sleep avg" value={fmtNumber(period?.sleepAvg, "h", 1)} sub={range} tone="teal" />
        <StatCard label="High risk" value={`${period?.highRiskDays ?? 0}d`} sub={range} tone="coral" />
        <StatCard label="Load trend" value={fmtNumber(period?.loadDelta, "", 1)} sub="acute delta" tone="amber" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_0.95fr]">
        <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">{range} trend</p>
              <h3 className="text-xl font-semibold">Recovery inputs</h3>
            </div>
            <TrendingUp className="text-teal" size={22} />
          </div>
          <MetricLineChart data={data.trends.daily_health.map((item) => ({ date: item.date, value: item.hrv_avg ?? null }))} color="#37c5ff" />
        </div>
        <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">{range} load</p>
            <h3 className="text-xl font-semibold">Acute vs chronic</h3>
          </div>
          <LoadChart data={data.trends.derived_metrics} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Period readout</p>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <Readout label="Days" value={String(data.trends.daily_health.length)} />
            <Readout label="Avg sleep" value={fmtNumber(period?.sleepAvg, "h", 1)} />
            <Readout label="Avg HRV" value={fmtNumber(period?.hrvAvg, "", 0)} />
            <Readout label="Avg stress" value={fmtNumber(period?.stressAvg, "", 0)} />
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
          <h3 className="text-base font-semibold">Recent activities</h3>
          <div className="mt-3 divide-y divide-line">
            {data.today.recent_activities.map((activity) => (
              <div key={activity.activity_id} className="grid grid-cols-[1fr_auto] gap-3 py-3 text-sm">
                <div>
                  <div className="font-medium text-ink">{activity.activity_name || activity.activity_type}</div>
                  <div className="text-muted">{activity.start_time?.slice(0, 10)} · {fmtDistance(activity.distance_meters)}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-coral">{fmtNumber(activity.training_load, "", 0)}</div>
                  <div className="text-muted">load</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Readout({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}

function buildPeriodSummary(trends: DashboardTrendsResponse) {
  const health = trends.daily_health;
  const metrics = trends.derived_metrics;
  return {
    sleepAvg: average(health.map((item) => item.sleep_hours)),
    hrvAvg: average(health.map((item) => item.hrv_avg)),
    rhrAvg: average(health.map((item) => item.resting_hr)),
    stressAvg: average(health.map((item) => item.stress_avg)),
    stepsAvg: average(health.map((item) => item.steps)),
    highRiskDays: metrics.filter((item) => item.risk_level === "high").length,
    loadDelta: delta(metrics.map((item) => item.acute_load_7d))
  };
}

function average(values: (number | null | undefined)[]) {
  const clean = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (!clean.length) return null;
  return clean.reduce((sum, value) => sum + value, 0) / clean.length;
}

function avgDefined(values: (number | null | undefined)[]) {
  return average(values);
}

function delta(values: (number | null | undefined)[]) {
  const clean = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (clean.length < 2) return null;
  return clean[clean.length - 1] - clean[0];
}

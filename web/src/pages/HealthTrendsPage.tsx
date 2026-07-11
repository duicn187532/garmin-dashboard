import { MetricLineChart } from "../charts/MetricLineChart";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { RangeTabs } from "../components/RangeTabs";
import { useAppData } from "../state/AppDataContext";
import { useState } from "react";

type Props = {
  apiBaseUrl: string;
};

const metrics = [
  { key: "sleep", label: "Sleep", color: "#1c6b5a" },
  { key: "hrv", label: "HRV", color: "#0f8f8a" },
  { key: "rhr", label: "RHR", color: "#b7791f" },
  { key: "stress", label: "Stress", color: "#c75b4a" },
  { key: "steps", label: "Steps", color: "#2f6d91" },
  { key: "body_battery", label: "Battery", color: "#725c3a" }
];

export function HealthTrendsPage({ apiBaseUrl }: Props) {
  const { cache, loading, error } = useAppData();
  const [metric, setMetric] = useState("sleep");
  const [range, setRange] = useState("30d");
  const selected = metrics.find((item) => item.key === metric) || metrics[0];
  const trends = cache.trendsByRange[range];
  const data = trends
    ? { metric, range, points: trends.daily_health.map((row) => ({ date: row.date, value: metricValue(row, metric) })) }
    : null;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold">Health Trends</h2>
        <RangeTabs value={range} onChange={setRange} />
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {metrics.map((item) => (
          <button
            key={item.key}
            className={`h-10 whitespace-nowrap rounded-xl border px-3 text-sm font-semibold ${
              metric === item.key ? "border-pine bg-pine text-surface" : "border-line bg-panel text-muted hover:bg-panel2 hover:text-ink"
            }`}
            onClick={() => setMetric(item.key)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        <h3 className="font-semibold">{selected.label}</h3>
        {loading ? <LoadingBlock /> : null}
        {error ? <EmptyState title="Trend unavailable" message={error} /> : null}
        {data ? <MetricLineChart data={data.points} color={selected.color} /> : null}
      </div>
    </section>
  );
}

function metricValue(row: { [key: string]: number | string | null | undefined }, metric: string) {
  if (metric === "sleep") return (row.sleep_hours as number | null | undefined) ?? null;
  if (metric === "hrv") return (row.hrv_avg as number | null | undefined) ?? null;
  if (metric === "rhr") return (row.resting_hr as number | null | undefined) ?? null;
  if (metric === "stress") return (row.stress_avg as number | null | undefined) ?? null;
  if (metric === "steps") return (row.steps as number | null | undefined) ?? null;
  if (metric === "body_battery") return (row.body_battery_max as number | null | undefined) ?? null;
  return null;
}

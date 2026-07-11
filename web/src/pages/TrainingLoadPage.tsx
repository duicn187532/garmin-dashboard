import { useState } from "react";
import { LoadChart } from "../charts/LoadChart";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { RangeTabs } from "../components/RangeTabs";
import { StatCard } from "../components/StatCard";
import { useAppData } from "../state/AppDataContext";
import { fmtNumber } from "../utils/format";

type Props = {
  apiBaseUrl: string;
};

export function TrainingLoadPage({ apiBaseUrl }: Props) {
  const { cache, loading, error } = useAppData();
  const [range, setRange] = useState("30d");
  const data = cache.trendsByRange[range] || null;
  const latest = data?.derived_metrics[data.derived_metrics.length - 1];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Training Load</h2>
        <RangeTabs value={range} onChange={setRange} />
      </div>
      {latest ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label="7d load" value={fmtNumber(latest.acute_load_7d, "", 1)} tone="coral" />
          <StatCard label="28d load" value={fmtNumber(latest.chronic_load_28d, "", 1)} tone="teal" />
          <StatCard label="ACWR" value={fmtNumber(latest.acwr, "", 2)} tone="amber" />
          <StatCard label="Risk" value={latest.risk_level || "NA"} tone="pine" />
        </div>
      ) : null}
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        {loading ? <LoadingBlock /> : null}
        {error ? <EmptyState title="Load unavailable" message={error} /> : null}
        {data?.derived_metrics.length ? (
          <LoadChart data={data.derived_metrics} />
        ) : (
          !loading && <EmptyState title="No load metrics" message="Run sync to calculate derived metrics." />
        )}
      </div>
    </section>
  );
}

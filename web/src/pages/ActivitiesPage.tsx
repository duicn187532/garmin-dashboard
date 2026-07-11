import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { useAppData } from "../state/AppDataContext";
import { fmtDateTime, fmtDistance, fmtDuration, fmtNumber } from "../utils/format";
import { ActivityDetailPage } from "./ActivityDetailPage";

type Props = {
  apiBaseUrl: string;
};

export function ActivitiesPage({ apiBaseUrl }: Props) {
  const { cache, loading, error, refreshFromBackend } = useAppData();
  const [selected, setSelected] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    start_date: "",
    end_date: "",
    activity_type: "",
    min_distance: "",
    min_avg_hr: "",
    min_training_load: ""
  });

  const data = useMemo(() => {
    const all = cache.activities?.items || [];
    const filtered = all.filter((activity) => {
      const activityDate = activity.start_time?.slice(0, 10) || "";
      if (filters.start_date && activityDate < filters.start_date) return false;
      if (filters.end_date && activityDate > filters.end_date) return false;
      if (filters.activity_type && !`${activity.activity_type || ""} ${activity.activity_name || ""}`.toLowerCase().includes(filters.activity_type.toLowerCase())) return false;
      if (filters.min_distance && (activity.distance_meters || 0) < Number(filters.min_distance) * 1000) return false;
      if (filters.min_avg_hr && (activity.average_hr || 0) < Number(filters.min_avg_hr)) return false;
      if (filters.min_training_load && (activity.training_load || 0) < Number(filters.min_training_load)) return false;
      return true;
    });
    return { items: filtered, total: filtered.length, page: 1, page_size: filtered.length };
  }, [cache.activities, filters]);

  if (selected) {
    return <ActivityDetailPage activityId={selected} apiBaseUrl={apiBaseUrl} onBack={() => setSelected(null)} />;
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Activities</h2>
        <button className="rounded-xl border border-line bg-panel2 px-3 py-2 text-sm font-semibold text-ink" onClick={() => refreshFromBackend({ sync: false })} type="button">
          Refresh cache
        </button>
      </div>
      <div className="rounded-2xl border border-line bg-panel/90 p-3 shadow-soft">
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
          <FilterInput label="From" type="date" value={filters.start_date} onChange={(value) => setFilters({ ...filters, start_date: value })} />
          <FilterInput label="To" type="date" value={filters.end_date} onChange={(value) => setFilters({ ...filters, end_date: value })} />
          <FilterInput label="Type" value={filters.activity_type} onChange={(value) => setFilters({ ...filters, activity_type: value })} />
          <FilterInput label="Min km" type="number" value={filters.min_distance} onChange={(value) => setFilters({ ...filters, min_distance: value })} />
          <FilterInput label="Min HR" type="number" value={filters.min_avg_hr} onChange={(value) => setFilters({ ...filters, min_avg_hr: value })} />
          <FilterInput label="Min load" type="number" value={filters.min_training_load} onChange={(value) => setFilters({ ...filters, min_training_load: value })} />
        </div>
      </div>
      {loading ? <LoadingBlock /> : null}
      {error ? <EmptyState title="Could not load activities" message={error} /> : null}
      {!loading && data?.items.length === 0 ? (
        <EmptyState title="No matching activities" message="Try clearing filters or run Garmin sync." />
      ) : null}
      <div className="space-y-2">
        {data?.items.map((activity) => (
          <button
            key={activity.activity_id}
            className="grid w-full grid-cols-[1fr_auto] gap-3 rounded-2xl border border-line bg-panel/90 p-4 text-left shadow-soft transition hover:border-pine/50"
            onClick={() => setSelected(activity.activity_id)}
            type="button"
          >
            <div>
              <div className="flex items-center gap-2">
                <Search size={16} className="text-pine" />
                <span className="font-semibold">{activity.activity_name || activity.activity_type || "Activity"}</span>
              </div>
              <div className="mt-1 text-sm text-muted">{fmtDateTime(activity.start_time)}</div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted">
                <span>{fmtDistance(activity.distance_meters)}</span>
                <span>{fmtDuration(activity.duration_seconds)}</span>
                <span>{fmtNumber(activity.average_hr, " bpm", 0)}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold">{fmtNumber(activity.training_load, "", 0)}</div>
              <div className="text-xs text-muted">load</div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-muted">{label}</span>
      <input
        className="mt-1 h-10 w-full rounded-xl border border-line bg-panel2 px-3 text-sm text-ink outline-none focus:border-pine"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

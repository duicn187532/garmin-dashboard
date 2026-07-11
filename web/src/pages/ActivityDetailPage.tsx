import { ArrowLeft } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatCard } from "../components/StatCard";
import { useResource } from "../hooks/useResource";
import { fmtDateTime, fmtDistance, fmtDuration, fmtNumber } from "../utils/format";

type Props = {
  activityId: string;
  apiBaseUrl: string;
  onBack: () => void;
};

export function ActivityDetailPage({ activityId, apiBaseUrl, onBack }: Props) {
  const { data, loading, error } = useResource(
    async () => {
      const [detail, laps, trackpoints] = await Promise.all([
        api.activityDetail(activityId, apiBaseUrl),
        api.activityLaps(activityId, apiBaseUrl),
        api.activityTrackpoints(activityId, apiBaseUrl)
      ]);
      return { detail, laps, trackpoints };
    },
    [activityId, apiBaseUrl]
  );

  if (loading) return <LoadingBlock />;
  if (error || !data) return <EmptyState title="Could not load activity" message={error || "Missing activity"} />;

  const chartData = data.trackpoints.map((point, index) => ({
    index,
    heart_rate: point.heart_rate,
    speed: point.speed ? point.speed * 3.6 : null
  }));
  const coords = data.trackpoints.filter((point) => point.latitude && point.longitude).slice(0, 6);

  return (
    <section className="space-y-4">
      <button className="inline-flex items-center gap-2 rounded-xl border border-line bg-panel2 px-3 py-2 text-sm text-ink" onClick={onBack} type="button">
        <ArrowLeft size={16} /> Back
      </button>
      <div>
        <h2 className="text-2xl font-semibold">{data.detail.activity_name || "Activity"}</h2>
        <p className="text-sm text-muted">{fmtDateTime(data.detail.start_time)}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Distance" value={fmtDistance(data.detail.distance_meters)} tone="pine" />
        <StatCard label="Duration" value={fmtDuration(data.detail.duration_seconds)} tone="teal" />
        <StatCard label="Avg HR" value={fmtNumber(data.detail.average_hr, " bpm", 0)} tone="amber" />
        <StatCard label="Load" value={fmtNumber(data.detail.training_load, "", 0)} tone="coral" />
      </div>
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        <h3 className="font-semibold">Heart rate and speed</h3>
        <div className="mt-3 h-72">
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
              <XAxis dataKey="index" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line dataKey="heart_rate" stroke="#c75b4a" strokeWidth={2} dot={false} name="HR" />
              <Line dataKey="speed" stroke="#0f8f8a" strokeWidth={2} dot={false} name="km/h" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        <h3 className="font-semibold">Laps</h3>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[620px] text-sm">
            <thead className="text-left text-xs uppercase text-muted">
              <tr>
                <th className="py-2">Lap</th>
                <th>Time</th>
                <th>Distance</th>
                <th>Avg HR</th>
                <th>Max HR</th>
                <th>Speed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.laps.map((lap) => (
                <tr key={lap.id}>
                  <td className="py-2">{lap.lap_index}</td>
                  <td>{fmtDuration(lap.duration_seconds)}</td>
                  <td>{fmtDistance(lap.distance_meters)}</td>
                  <td>{fmtNumber(lap.average_hr, "", 0)}</td>
                  <td>{fmtNumber(lap.max_hr, "", 0)}</td>
                  <td>{fmtNumber(lap.average_speed ? lap.average_speed * 3.6 : null, " km/h", 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        <h3 className="font-semibold">Trackpoints map placeholder</h3>
        <p className="mt-2 text-sm text-muted">
          {data.trackpoints.length} trackpoints available. Map provider can be added here without changing the API.
        </p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {coords.map((point) => (
            <div key={point.id} className="rounded-xl border border-line bg-panel2 p-3 text-sm">
              <div>{point.timestamp?.slice(11, 19)}</div>
              <div className="text-muted">
                {point.latitude}, {point.longitude}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

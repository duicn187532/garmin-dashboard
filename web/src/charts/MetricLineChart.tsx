import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = {
  data: { date: string; value: number | null }[];
  color?: string;
};

export function MetricLineChart({ data, color = "#1c6b5a" }: Props) {
  const chartData = data.map((item) => ({ ...item, label: item.date.slice(5) }));
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 10, right: 8, bottom: 0, left: -16 }}>
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#91a1b6" }} axisLine={{ stroke: "#25324a" }} />
          <YAxis tick={{ fontSize: 12, fill: "#91a1b6" }} axisLine={{ stroke: "#25324a" }} />
          <Tooltip contentStyle={{ background: "#101827", border: "1px solid #25324a", borderRadius: 12 }} />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

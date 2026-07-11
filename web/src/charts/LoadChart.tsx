import { Area, AreaChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DerivedMetric } from "../types/api";

type Props = {
  data: DerivedMetric[];
};

export function LoadChart({ data }: Props) {
  const chartData = data.map((item) => ({
    date: item.date.slice(5),
    acute: item.acute_load_7d,
    chronic: item.chronic_load_28d,
    acwr: item.acwr
  }));
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 10, right: 8, bottom: 0, left: -16 }}>
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#91a1b6" }} axisLine={{ stroke: "#25324a" }} />
          <YAxis tick={{ fontSize: 12, fill: "#91a1b6" }} axisLine={{ stroke: "#25324a" }} />
          <Tooltip contentStyle={{ background: "#101827", border: "1px solid #25324a", borderRadius: 12 }} />
          <Area dataKey="chronic" fill="rgba(55,197,255,0.18)" stroke="#37c5ff" strokeWidth={2} name="28d load" />
          <Line dataKey="acute" stroke="#ff766f" strokeWidth={2} dot={false} name="7d load" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

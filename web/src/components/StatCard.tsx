type Props = {
  label: string;
  value: string;
  sub?: string;
  tone?: "pine" | "teal" | "amber" | "coral";
};

const toneMap = {
  pine: "border-pine/25 bg-pine/10 text-pine",
  teal: "border-teal/25 bg-teal/10 text-teal",
  amber: "border-amber/25 bg-amber/10 text-amber",
  coral: "border-coral/25 bg-coral/10 text-coral"
};

export function StatCard({ label, value, sub, tone = "pine" }: Props) {
  return (
    <div className={`rounded-xl border p-4 shadow-soft ${toneMap[tone]}`}>
      <div className="text-xs font-medium uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-ink">{value}</div>
      {sub ? <div className="mt-1 text-xs text-muted">{sub}</div> : null}
    </div>
  );
}

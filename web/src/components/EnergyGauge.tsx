type Props = {
  label: string;
  value?: number | null;
  max?: number;
  unit?: string;
  helper?: string;
  tone?: "pine" | "teal" | "amber" | "coral" | "violet";
};

const toneColor = {
  pine: "#43d6a4",
  teal: "#37c5ff",
  amber: "#f8c75c",
  coral: "#ff766f",
  violet: "#9c8cff"
};

export function EnergyGauge({ label, value, max = 100, unit = "", helper, tone = "pine" }: Props) {
  const safeValue = typeof value === "number" && Number.isFinite(value) ? value : null;
  const percent = safeValue === null ? 0 : Math.max(0, Math.min(100, (safeValue / max) * 100));
  const color = toneColor[tone];

  return (
    <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
          {helper ? <p className="mt-1 text-xs text-muted">{helper}</p> : null}
        </div>
        <div className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
      </div>
      <div className="mt-4 flex justify-center">
        <div
          className="relative grid aspect-square w-32 place-items-center rounded-full sm:w-36"
          style={{
            background: `conic-gradient(${color} ${percent * 3.6}deg, rgba(255,255,255,0.08) 0deg)`
          }}
        >
          <div className="absolute inset-3 rounded-full bg-surface shadow-inner" />
          <div className="relative text-center">
            <div className="text-3xl font-semibold text-ink">
              {safeValue === null ? "NA" : safeValue.toFixed(max <= 10 ? 2 : 0)}
            </div>
            {safeValue !== null && unit ? <div className="text-xs font-medium text-muted">{unit}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}


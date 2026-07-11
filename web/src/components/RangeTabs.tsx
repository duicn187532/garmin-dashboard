type Props = {
  value: string;
  onChange: (value: string) => void;
};

const ranges = ["7d", "30d", "90d"];

export function RangeTabs({ value, onChange }: Props) {
  return (
    <div className="inline-flex rounded-xl border border-line bg-panel p-1 shadow-soft">
      {ranges.map((item) => (
        <button
          key={item}
          className={`h-9 min-w-14 rounded-md px-3 text-sm font-medium ${
            value === item ? "bg-pine text-surface" : "text-muted hover:bg-panel2 hover:text-ink"
          }`}
          onClick={() => onChange(item)}
          type="button"
        >
          {item}
        </button>
      ))}
    </div>
  );
}

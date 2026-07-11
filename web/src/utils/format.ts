export function fmtNumber(value?: number | null, suffix = "", digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "NA";
  return `${value.toFixed(digits)}${suffix}`;
}

export function fmtDistance(meters?: number | null): string {
  if (!meters) return "NA";
  return `${(meters / 1000).toFixed(1)} km`;
}

export function fmtDuration(seconds?: number | null): string {
  if (!seconds) return "NA";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  return hours ? `${hours}h ${minutes}m` : `${minutes}m`;
}

export function fmtDateTime(value?: string | null): string {
  if (!value) return "NA";
  return new Intl.DateTimeFormat("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function riskTone(risk?: string | null): string {
  if (risk === "high") return "text-coral bg-coral/10 border-coral/25";
  if (risk === "medium") return "text-amber bg-amber/10 border-amber/25";
  return "text-pine bg-pine/10 border-pine/25";
}

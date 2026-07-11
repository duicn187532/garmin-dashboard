export function fmtNumber(value?: number | null, suffix = "", digits = 0) {
  if (value === undefined || value === null || Number.isNaN(value)) return "NA";
  return `${value.toFixed(digits)}${suffix}`;
}

export function fmtDistance(meters?: number | null) {
  if (!meters) return "NA";
  return `${(meters / 1000).toFixed(1)} km`;
}

export function fmtDate(value?: string | null) {
  if (!value) return "NA";
  return value.slice(0, 10);
}


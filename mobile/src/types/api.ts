export type Activity = {
  id: number;
  activity_id: string;
  activity_type?: string | null;
  activity_name?: string | null;
  start_time?: string | null;
  duration_seconds?: number | null;
  distance_meters?: number | null;
  average_hr?: number | null;
  training_load?: number | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export type ActivityListResponse = {
  items: Activity[];
  total: number;
  page: number;
  page_size: number;
};

export type DailyHealth = {
  id: number;
  date: string;
  steps?: number | null;
  resting_hr?: number | null;
  sleep_hours?: number | null;
  stress_avg?: number | null;
  body_battery_min?: number | null;
  body_battery_max?: number | null;
  hrv_avg?: number | null;
  created_at: string;
  updated_at: string;
};

export type DerivedMetric = {
  id: number;
  date: string;
  acute_load_7d?: number | null;
  chronic_load_28d?: number | null;
  acwr?: number | null;
  recovery_score?: number | null;
  risk_level?: string | null;
};

export type AiReport = {
  id: number;
  report_date: string;
  report_type: string;
  question?: string | null;
  answer: string;
  evidence_json: Record<string, unknown>;
  model: string;
  created_at: string;
};

export type TodayResponse = {
  health: DailyHealth | null;
  derived_metric: DerivedMetric | null;
  ai_report: AiReport | null;
  recent_activities: Activity[];
};

export type DashboardTrendsResponse = {
  range: string;
  daily_health: DailyHealth[];
  derived_metrics: DerivedMetric[];
};


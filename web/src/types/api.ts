export type Activity = {
  id: number;
  activity_id: string;
  activity_type?: string | null;
  activity_name?: string | null;
  start_time?: string | null;
  duration_seconds?: number | null;
  distance_meters?: number | null;
  average_hr?: number | null;
  max_hr?: number | null;
  calories?: number | null;
  average_speed?: number | null;
  elevation_gain?: number | null;
  training_load?: number | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export type ActivityDetail = Activity & {
  laps_count: number;
  trackpoints_count: number;
};

export type ActivityLap = {
  id: number;
  activity_id: string;
  lap_index: number;
  start_time?: string | null;
  duration_seconds?: number | null;
  distance_meters?: number | null;
  average_hr?: number | null;
  max_hr?: number | null;
  average_speed?: number | null;
  calories?: number | null;
};

export type ActivityTrackpoint = {
  id: number;
  activity_id: string;
  timestamp?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  heart_rate?: number | null;
  speed?: number | null;
  distance_meters?: number | null;
  altitude?: number | null;
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
  stress_max?: number | null;
  body_battery_min?: number | null;
  body_battery_max?: number | null;
  hrv_avg?: number | null;
  intensity_minutes?: number | null;
  calories?: number | null;
  weight?: number | null;
  created_at: string;
  updated_at: string;
};

export type DerivedMetric = {
  id: number;
  date: string;
  acute_load_7d?: number | null;
  chronic_load_28d?: number | null;
  acwr?: number | null;
  sleep_7d_avg?: number | null;
  hrv_7d_avg?: number | null;
  rhr_7d_avg?: number | null;
  recovery_score?: number | null;
  risk_level?: "low" | "medium" | "high" | string | null;
  notes_json?: Record<string, unknown>;
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
  recent_activities: Pick<
    Activity,
    "activity_id" | "activity_type" | "activity_name" | "start_time" | "training_load" | "distance_meters" | "average_hr"
  >[];
};

export type DashboardTrendsResponse = {
  range: string;
  daily_health: DailyHealth[];
  derived_metrics: DerivedMetric[];
};


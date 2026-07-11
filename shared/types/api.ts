export type RangeKey = "7d" | "30d" | "90d";
export type RiskLevel = "low" | "medium" | "high";

export type GarminInsightStatus = {
  status: "ok";
  app: string;
  environment: string;
  demo_mode: boolean;
  time: string;
};

export type SyncResponse = {
  status: string;
  source: string;
  activities_created: number;
  activities_updated: number;
  daily_health_created: number;
  daily_health_updated: number;
  derived_metrics_updated: number;
  message?: string | null;
};


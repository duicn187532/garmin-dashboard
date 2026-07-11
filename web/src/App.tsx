import { useState } from "react";
import { getApiBaseUrl } from "./api/client";
import { AppShell, type ViewKey } from "./components/AppShell";
import { ActivitiesPage } from "./pages/ActivitiesPage";
import { AICoachPage } from "./pages/AICoachPage";
import { HealthTrendsPage } from "./pages/HealthTrendsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TodayPage } from "./pages/TodayPage";
import { TrainingLoadPage } from "./pages/TrainingLoadPage";
import { AppDataProvider } from "./state/AppDataContext";

export default function App() {
  const [view, setView] = useState<ViewKey>("today");
  const [apiBaseUrl, setApiBaseUrl] = useState(getApiBaseUrl());

  return (
    <AppDataProvider apiBaseUrl={apiBaseUrl}>
      <AppShell view={view} onViewChange={setView}>
        {view === "today" ? <TodayPage apiBaseUrl={apiBaseUrl} /> : null}
        {view === "activities" ? <ActivitiesPage apiBaseUrl={apiBaseUrl} /> : null}
        {view === "trends" ? <HealthTrendsPage apiBaseUrl={apiBaseUrl} /> : null}
        {view === "load" ? <TrainingLoadPage apiBaseUrl={apiBaseUrl} /> : null}
        {view === "ai" ? <AICoachPage apiBaseUrl={apiBaseUrl} /> : null}
        {view === "settings" ? <SettingsPage apiBaseUrl={apiBaseUrl} onApiBaseUrlChange={setApiBaseUrl} /> : null}
      </AppShell>
    </AppDataProvider>
  );
}

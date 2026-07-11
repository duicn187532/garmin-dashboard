import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { PrimaryButton } from "../components/PrimaryButton";
import { Screen } from "../components/Screen";
import { StatTile } from "../components/StatTile";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { fmtNumber } from "../utils/format";

export function TodayScreen() {
  const { data, loading, error, reload } = useAsyncResource(api.today);
  const [busy, setBusy] = useState(false);

  async function runSync() {
    setBusy(true);
    try {
      await api.sync(30);
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function runAI() {
    setBusy(true);
    try {
      await api.analyze();
      reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen title="Today">
      {loading ? <EmptyState title="Loading" loading /> : null}
      {error ? <EmptyState title="Backend unavailable" message={error} /> : null}
      {!loading && !data?.health ? <EmptyState title="No data" message="Run sync to load demo data." /> : null}
      {data?.health ? (
        <>
          <View style={styles.grid}>
            <StatTile label="Sleep" value={fmtNumber(data.health.sleep_hours, "h", 1)} />
            <StatTile label="HRV" value={fmtNumber(data.health.hrv_avg, "", 0)} />
            <StatTile label="RHR" value={fmtNumber(data.health.resting_hr, "", 0)} />
            <StatTile label="Stress" value={fmtNumber(data.health.stress_avg, "", 0)} />
            <StatTile label="ACWR" value={fmtNumber(data.derived_metric?.acwr, "", 2)} />
            <StatTile label="Recovery" value={fmtNumber(data.derived_metric?.recovery_score, "", 0)} />
          </View>
          <View style={styles.panel}>
            <Text style={styles.panelTitle}>AI recommendation</Text>
            <Text style={styles.body}>{data.ai_report?.answer || "Run AI analysis after syncing."}</Text>
          </View>
        </>
      ) : null}
      <View style={styles.actions}>
        <PrimaryButton onPress={runSync} disabled={busy}>
          Sync
        </PrimaryButton>
        <PrimaryButton onPress={runAI} disabled={busy} variant="secondary">
          Analyze
        </PrimaryButton>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between"
  },
  panel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 14,
    marginTop: 6
  },
  panelTitle: {
    color: "#1c6b5a",
    fontWeight: "700",
    marginBottom: 8
  },
  body: {
    color: "#18201e",
    lineHeight: 22
  },
  actions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  }
});


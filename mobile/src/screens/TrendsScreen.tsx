import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { api } from "../api/client";
import { SimpleLineChart } from "../charts/SimpleLineChart";
import { EmptyState } from "../components/EmptyState";
import { Screen } from "../components/Screen";
import { useAsyncResource } from "../hooks/useAsyncResource";

const ranges = ["7d", "30d", "90d"];
const metrics = ["sleep", "hrv", "rhr", "stress", "steps", "body_battery"];

export function TrendsScreen() {
  const [range, setRange] = useState("30d");
  const [metric, setMetric] = useState("sleep");
  const { data, loading, error } = useAsyncResource(() => api.trends(range), [range]);
  const points = useMemo(() => {
    const health = data?.daily_health || [];
    return health.map((row) => ({
      date: row.date,
      value:
        metric === "sleep"
          ? row.sleep_hours ?? null
          : metric === "hrv"
            ? row.hrv_avg ?? null
            : metric === "rhr"
              ? row.resting_hr ?? null
              : metric === "stress"
                ? row.stress_avg ?? null
                : metric === "steps"
                  ? row.steps ?? null
                  : row.body_battery_max ?? null
    }));
  }, [data, metric]);

  return (
    <Screen title="Trends">
      <Segment values={ranges} value={range} onChange={setRange} />
      <Segment values={metrics} value={metric} onChange={setMetric} />
      {loading ? <EmptyState title="Loading" loading /> : null}
      {error ? <EmptyState title="Trend unavailable" message={error} /> : null}
      {!loading && !error ? (
        <View style={styles.panel}>
          <Text style={styles.title}>{metric}</Text>
          <SimpleLineChart points={points} />
        </View>
      ) : null}
    </Screen>
  );
}

function Segment({ values, value, onChange }: { values: string[]; value: string; onChange: (value: string) => void }) {
  return (
    <View style={styles.segment}>
      {values.map((item) => (
        <Pressable key={item} onPress={() => onChange(item)} style={[styles.segmentButton, item === value ? styles.active : null]}>
          <Text style={[styles.segmentText, item === value ? styles.activeText : null]}>{item}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  segment: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 12
  },
  segmentButton: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    paddingHorizontal: 12,
    paddingVertical: 9
  },
  active: {
    backgroundColor: "#1c6b5a",
    borderColor: "#1c6b5a"
  },
  segmentText: {
    color: "#4f5754",
    fontWeight: "700"
  },
  activeText: {
    color: "#ffffff"
  },
  panel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 14
  },
  title: {
    color: "#18201e",
    fontWeight: "700",
    fontSize: 18,
    marginBottom: 8
  }
});


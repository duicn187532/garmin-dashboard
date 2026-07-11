import { FlatList, StyleSheet, Text, View } from "react-native";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { Screen } from "../components/Screen";
import { useAsyncResource } from "../hooks/useAsyncResource";
import type { Activity } from "../types/api";
import { fmtDate, fmtDistance, fmtNumber } from "../utils/format";

export function ActivitiesScreen() {
  const { data, loading, error } = useAsyncResource(api.activities);
  return (
    <Screen title="Activities">
      {loading ? <EmptyState title="Loading" loading /> : null}
      {error ? <EmptyState title="Could not load activities" message={error} /> : null}
      {!loading && data?.items.length === 0 ? <EmptyState title="No activities" message="Run sync from Today." /> : null}
      <FlatList
        data={data?.items || []}
        keyExtractor={(item) => item.activity_id}
        scrollEnabled={false}
        renderItem={({ item }) => <ActivityRow activity={item} />}
      />
    </Screen>
  );
}

function ActivityRow({ activity }: { activity: Activity }) {
  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.main}>
          <Text style={styles.title}>{activity.activity_name || activity.activity_type || "Activity"}</Text>
          <Text style={styles.muted}>{fmtDate(activity.start_time)}</Text>
        </View>
        <View style={styles.load}>
          <Text style={styles.loadValue}>{fmtNumber(activity.training_load, "", 0)}</Text>
          <Text style={styles.muted}>load</Text>
        </View>
      </View>
      <View style={styles.meta}>
        <Text style={styles.metaText}>{fmtDistance(activity.distance_meters)}</Text>
        <Text style={styles.metaText}>{fmtNumber(activity.average_hr, " bpm", 0)}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 14,
    marginBottom: 10
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12
  },
  main: {
    flex: 1
  },
  title: {
    color: "#18201e",
    fontWeight: "700",
    fontSize: 16
  },
  muted: {
    color: "#767b75",
    marginTop: 2
  },
  load: {
    alignItems: "flex-end"
  },
  loadValue: {
    color: "#c75b4a",
    fontSize: 20,
    fontWeight: "700"
  },
  meta: {
    flexDirection: "row",
    gap: 12,
    marginTop: 10
  },
  metaText: {
    color: "#4f5754"
  }
});


import { Dimensions, StyleSheet, Text, View } from "react-native";
import { LineChart } from "react-native-chart-kit";

type Props = {
  points: { date: string; value: number | null }[];
};

export function SimpleLineChart({ points }: Props) {
  const filtered = points.filter((item) => item.value !== null) as { date: string; value: number }[];
  if (filtered.length < 2) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>Not enough points</Text>
      </View>
    );
  }

  return (
    <LineChart
      data={{
        labels: filtered.map((item) => item.date.slice(5)).slice(-6),
        datasets: [{ data: filtered.map((item) => item.value).slice(-6) }]
      }}
      width={Dimensions.get("window").width - 32}
      height={220}
      yAxisInterval={1}
      chartConfig={{
        backgroundColor: "#ffffff",
        backgroundGradientFrom: "#ffffff",
        backgroundGradientTo: "#ffffff",
        decimalPlaces: 0,
        color: () => "#1c6b5a",
        labelColor: () => "#767b75",
        propsForDots: { r: "3", strokeWidth: "1", stroke: "#1c6b5a" }
      }}
      bezier
      style={styles.chart}
    />
  );
}

const styles = StyleSheet.create({
  chart: {
    borderRadius: 8,
    marginLeft: -16
  },
  empty: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    padding: 16,
    alignItems: "center"
  },
  emptyText: {
    color: "#767b75"
  }
});


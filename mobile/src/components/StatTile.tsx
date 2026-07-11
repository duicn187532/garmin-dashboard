import { StyleSheet, Text, View } from "react-native";

type Props = {
  label: string;
  value: string;
  sub?: string;
};

export function StatTile({ label, value, sub }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      {sub ? <Text style={styles.sub}>{sub}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexBasis: "48%",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 12,
    marginBottom: 10
  },
  label: {
    color: "#767b75",
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase"
  },
  value: {
    color: "#18201e",
    fontSize: 24,
    fontWeight: "700",
    marginTop: 4
  },
  sub: {
    color: "#767b75",
    fontSize: 12,
    marginTop: 3
  }
});


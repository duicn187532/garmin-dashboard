import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

type Props = {
  title: string;
  message?: string;
  loading?: boolean;
};

export function EmptyState({ title, message, loading }: Props) {
  return (
    <View style={styles.box}>
      {loading ? <ActivityIndicator color="#1c6b5a" /> : null}
      <Text style={styles.title}>{title}</Text>
      {message ? <Text style={styles.message}>{message}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 16,
    alignItems: "center"
  },
  title: {
    color: "#18201e",
    fontWeight: "700",
    marginTop: 8
  },
  message: {
    color: "#767b75",
    textAlign: "center",
    marginTop: 6
  }
});


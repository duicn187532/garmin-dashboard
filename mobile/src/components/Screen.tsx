import type { ReactNode } from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

type Props = {
  title: string;
  children: ReactNode;
};

export function Screen({ title, children }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.brand}>Garmin Insight</Text>
          <Text style={styles.title}>{title}</Text>
        </View>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f7f8f5"
  },
  content: {
    padding: 16,
    paddingBottom: 120
  },
  header: {
    marginBottom: 16
  },
  brand: {
    color: "#1c6b5a",
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase"
  },
  title: {
    color: "#18201e",
    fontSize: 28,
    fontWeight: "700",
    marginTop: 4
  }
});


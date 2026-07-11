import { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { PrimaryButton } from "../components/PrimaryButton";
import { Screen } from "../components/Screen";
import { useAsyncResource } from "../hooks/useAsyncResource";
import type { AiReport } from "../types/api";

export function AIScreen() {
  const { data, loading, error, reload } = useAsyncResource(api.latestAi);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AiReport | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    if (!question.trim()) return;
    setBusy(true);
    try {
      const report = await api.ask(question.trim());
      setAnswer(report);
      setQuestion("");
      reload();
    } finally {
      setBusy(false);
    }
  }

  const report = answer || data;
  return (
    <Screen title="AI Coach">
      <View style={styles.inputPanel}>
        <TextInput
          style={styles.input}
          value={question}
          onChangeText={setQuestion}
          placeholder="最近 14 天恢復如何？"
          multiline
        />
        <PrimaryButton onPress={ask} disabled={busy}>
          Ask
        </PrimaryButton>
      </View>
      {loading ? <EmptyState title="Loading" loading /> : null}
      {error ? <EmptyState title="AI unavailable" message={error} /> : null}
      {report ? (
        <View style={styles.report}>
          <Text style={styles.type}>{report.report_type}</Text>
          <Text style={styles.answer}>{report.answer}</Text>
          <Text style={styles.model}>Model: {report.model}</Text>
        </View>
      ) : (
        !loading && <EmptyState title="No report" message="Ask a question or run analysis from Today." />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  inputPanel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 12,
    marginBottom: 12,
    gap: 10
  },
  input: {
    minHeight: 76,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    padding: 10,
    color: "#18201e"
  },
  report: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 14
  },
  type: {
    color: "#1c6b5a",
    fontWeight: "700",
    textTransform: "uppercase"
  },
  answer: {
    color: "#18201e",
    lineHeight: 22,
    marginTop: 10
  },
  model: {
    color: "#767b75",
    marginTop: 12
  }
});


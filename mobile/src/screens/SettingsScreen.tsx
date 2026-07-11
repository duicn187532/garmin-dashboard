import { useEffect, useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { api, getApiBaseUrl, getAppAccessToken, getSyncToken, setApiBaseUrl, setAppAccessToken, setSyncToken } from "../api/client";
import { PrimaryButton } from "../components/PrimaryButton";
import { Screen } from "../components/Screen";

export function SettingsScreen() {
  const [baseUrl, setBaseUrlValue] = useState("http://127.0.0.1:8000");
  const [appToken, setAppTokenValue] = useState("");
  const [token, setTokenValue] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    getApiBaseUrl().then(setBaseUrlValue);
    getAppAccessToken().then(setAppTokenValue);
    getSyncToken().then(setTokenValue);
  }, []);

  async function save() {
    await setApiBaseUrl(baseUrl);
    await setAppAccessToken(appToken);
    await setSyncToken(token);
    setStatus("Saved locally");
  }

  async function test() {
    const result = await api.status();
    setStatus(`Backend ${result.status}`);
  }

  return (
    <Screen title="Settings">
      <View style={styles.panel}>
        <Text style={styles.label}>API Base URL</Text>
        <TextInput style={styles.input} value={baseUrl} onChangeText={setBaseUrlValue} autoCapitalize="none" />
        <Text style={styles.hint}>iOS simulator can use 127.0.0.1. Expo Go on a device usually needs your LAN IP.</Text>
        <Text style={styles.label}>App access token</Text>
        <TextInput style={styles.input} value={appToken} onChangeText={setAppTokenValue} secureTextEntry autoCapitalize="none" />
        <Text style={styles.label}>Sync token</Text>
        <TextInput style={styles.input} value={token} onChangeText={setTokenValue} secureTextEntry autoCapitalize="none" />
        <View style={styles.actions}>
          <PrimaryButton onPress={save}>Save</PrimaryButton>
          <PrimaryButton onPress={test} variant="secondary">
            Test
          </PrimaryButton>
        </View>
        {status ? <Text style={styles.status}>{status}</Text> : null}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    backgroundColor: "#ffffff",
    padding: 14,
    gap: 10
  },
  label: {
    color: "#4f5754",
    fontWeight: "700"
  },
  input: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d9ded6",
    paddingHorizontal: 10
  },
  hint: {
    color: "#767b75",
    lineHeight: 20
  },
  actions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 6
  },
  status: {
    color: "#1c6b5a",
    fontWeight: "700"
  }
});

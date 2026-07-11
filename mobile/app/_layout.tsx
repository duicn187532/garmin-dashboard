import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";

type IconName = keyof typeof Ionicons.glyphMap;

function tabIcon(name: IconName) {
  return ({ color, size }: { color: string; size: number }) => <Ionicons name={name} size={size} color={color} />;
}

export default function RootLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#1c6b5a",
        tabBarInactiveTintColor: "#767b75",
        tabBarStyle: { height: 68, paddingBottom: 10, paddingTop: 8 }
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Today", tabBarIcon: tabIcon("today-outline") }} />
      <Tabs.Screen name="activities" options={{ title: "Activities", tabBarIcon: tabIcon("bicycle-outline") }} />
      <Tabs.Screen name="trends" options={{ title: "Trends", tabBarIcon: tabIcon("pulse-outline") }} />
      <Tabs.Screen name="ai" options={{ title: "AI", tabBarIcon: tabIcon("sparkles-outline") }} />
      <Tabs.Screen name="settings" options={{ title: "Settings", tabBarIcon: tabIcon("settings-outline") }} />
    </Tabs>
  );
}


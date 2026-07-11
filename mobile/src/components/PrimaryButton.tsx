import type { ReactNode } from "react";
import { Pressable, StyleSheet, Text } from "react-native";

type Props = {
  children: ReactNode;
  onPress: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary";
};

export function PrimaryButton({ children, onPress, disabled, variant = "primary" }: Props) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={[styles.button, variant === "secondary" ? styles.secondary : styles.primary, disabled ? styles.disabled : null]}
    >
      <Text style={[styles.text, variant === "secondary" ? styles.secondaryText : styles.primaryText]}>{children}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 44,
    borderRadius: 8,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center"
  },
  primary: {
    backgroundColor: "#1c6b5a"
  },
  secondary: {
    backgroundColor: "#ffffff",
    borderColor: "#d9ded6",
    borderWidth: 1
  },
  disabled: {
    opacity: 0.65
  },
  text: {
    fontWeight: "700"
  },
  primaryText: {
    color: "#ffffff"
  },
  secondaryText: {
    color: "#18201e"
  }
});


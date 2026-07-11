/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#f4f7fb",
        muted: "#91a1b6",
        surface: "#070b12",
        panel: "#101827",
        panel2: "#162033",
        line: "#25324a",
        pine: "#43d6a4",
        teal: "#37c5ff",
        amber: "#f8c75c",
        coral: "#ff766f",
        violet: "#9c8cff"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(0, 0, 0, 0.28)",
        glow: "0 0 36px rgba(67, 214, 164, 0.18)"
      }
    }
  },
  plugins: []
};

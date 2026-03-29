import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 18px 40px -28px rgba(13, 24, 36, 0.45)",
      },
    },
  },
  plugins: [],
};

export default config;

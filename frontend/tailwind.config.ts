import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8f4",
          100: "#d8efe5",
          600: "#24785c",
          700: "#1d604a",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;

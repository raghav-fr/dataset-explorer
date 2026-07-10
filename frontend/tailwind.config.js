/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#12141a",
        panel: "#1a1d26",
        panel2: "#20232e",
        line: "#2b2f3c",
        amber: {
          400: "#f2b84b",
          500: "#e8a52c",
        },
        ink: {
          100: "#f4f5f7",
          300: "#b7bccb",
          500: "#7d8299",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        grid: "linear-gradient(#20232e 1px, transparent 1px), linear-gradient(90deg, #20232e 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "24px 24px",
      },
    },
  },
  plugins: [],
};

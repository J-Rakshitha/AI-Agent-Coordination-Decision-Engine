/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // These map to CSS variables (defined in src/styles/index.css) so
        // toggling the "light" class on <html> instantly re-themes every
        // component that uses these tokens — no per-component dark: variants needed.
        base: {
          bg: "var(--color-bg)",
          surface: "var(--color-surface)",
          border: "var(--color-border)",
        },
        ink: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
          faint: "var(--text-faint)",
        },
        accent: {
          devcollab: "#4F8CFF",   // blue = development phase
          aiops: "#FF6B6B",       // red/coral = production/incident phase
          success: "#3ECF8E",
          warning: "#F5A623",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

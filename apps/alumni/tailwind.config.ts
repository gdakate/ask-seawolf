/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        sbu: {
          red: "#990000",
          "red-dark": "#7a0000",
          "red-light": "#cc3333",
          gray: {
            50: "#f8f9fa",
            100: "#f1f3f5",
            200: "#e9ecef",
            300: "#dee2e6",
            400: "#ced4da",
            500: "#adb5bd",
            600: "#868e96",
            700: "#495057",
            800: "#343a40",
            900: "#212529",
          },
        },
        water: {
          surface:  "#f0f9ff",
          sky:      "#e0f2fe",
          shallow:  "#bae6fd",
          foam:     "#7dd3fc",
          current:  "#0ea5e9",
          deep:     "#0369a1",
          deeper:   "#075985",
          abyss:    "#0c2340",
          teal:     "#0891b2",
          shimmer:  "#22d3ee",
          glow:     "#67e8f9",
          midnight: "#020c1b",
        },
      },
      fontFamily: {
        sans: ['"Source Sans 3"', "system-ui", "sans-serif"],
        display: ['"Playfair Display"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      keyframes: {
        waterFlow: {
          "0%, 100%": { backgroundPosition: "0% 60%" },
          "50%":       { backgroundPosition: "100% 40%" },
        },
        bubbleRise: {
          "0%":   { transform: "translateY(0) scale(1)",   opacity: "0.5" },
          "100%": { transform: "translateY(-80px) scale(0.3)", opacity: "0" },
        },
        shimmerSweep: {
          "0%":   { transform: "translateX(-100%) skewX(-15deg)" },
          "100%": { transform: "translateX(300%) skewX(-15deg)" },
        },
        depthPulse: {
          "0%, 100%": { opacity: "0.3" },
          "50%":       { opacity: "0.65" },
        },
      },
      animation: {
        "water-flow":    "waterFlow 14s ease infinite",
        "bubble-rise":   "bubbleRise 3s ease-in infinite",
        "shimmer-sweep": "shimmerSweep 2.4s ease infinite",
        "depth-pulse":   "depthPulse 4s ease infinite",
      },
    },
  },
  plugins: [],
};

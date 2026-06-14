/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
    "./static/js/**/*.js",
  ],
  darkMode: "class",
  safelist: [
    // dark-mode retint targets + reveal delays referenced indirectly
    "dark:bg-gray-700", "dark:bg-gray-800", "dark:bg-gray-900", "dark:bg-black",
  ],
  theme: {
    extend: {
      colors: {
        ivory: "#F8F4EF",
        cream: "#FBF8F4",
        sand: "#F1E7D7",
        blush: "#E8CFCF",
        lavender: "#D8D0E8",
        gold: "#B8945A",
        "gold-soft": "#C9A86A",
        charcoal: "#2B2B2B",
        ink: "#161310",
        "d-bg": "#161310",
        "d-surface": "#1E1A17",
        "d-card": "#262220",
        line: "#E6DFD5",
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', "Playfair Display", "Georgia", "serif"],
        display: ["Playfair Display", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      letterSpacing: {
        luxe: "0.22em",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};

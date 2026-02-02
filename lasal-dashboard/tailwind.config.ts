import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}", // Added src/ for safety as we are using src dir
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          mint: "#95E1D3",
          sand: "#FDFCF8",
          beige: "#F5E9E2",
          dark: "#2D2D2D",
          text: "#333333",
          success: "#22c55e",
          warning: "#eab308",
          danger: "#ef4444"
        }
      },
      fontFamily: {
        serif: ['var(--font-playfair)', 'serif'],
        sans: ['var(--font-inter)', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
export default config;

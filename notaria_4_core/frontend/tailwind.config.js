/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'notaria-navy': '#002D62',
        'notaria-gold': '#C5A049',
      }
    },
  },
  plugins: [],
}

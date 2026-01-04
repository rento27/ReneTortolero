/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          600: '#002D62',
          700: '#002552',
          800: '#001D41',
          900: '#001530',
        },
        gold: {
          100: '#F9F1D8',
          500: '#C5A049',
          700: '#9E803A',
        },
        sand: {
          50: '#FDFCF8',
          200: '#EFECE0',
        }
      },
      fontFamily: {
        serif: ['Playfair Display', 'serif'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

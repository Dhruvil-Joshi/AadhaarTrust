/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        purple: {
          primary: '#7C3AED',
          light: '#A78BFA',
          accent: '#8B5CF6',
        },
      },
    },
  },
  plugins: [],
}

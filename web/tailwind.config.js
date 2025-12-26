/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--bg-primary)',
        'primary-text': 'var(--text-primary)',
        'border': 'var(--border-color)',
      },
    },
  },
  plugins: [],
}

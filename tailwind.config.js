/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/**/*.{html,js}",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        'legacy-blue': '#3B82F6',
        'legacy-green': '#34D399',
        'legacy-purple': '#8B5CF6'
      }
    }
  },
  plugins: []
}
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#FAFAF8',
        ink: '#1A1A1A',
        muted: '#666666',
        primary: '#2B4C7E',
        amber: '#E8A838',
        success: '#4CAF78',
        danger: '#E85D4A',
        soft: '#F0F0EC',
      },
      boxShadow: {
        soft: '0 18px 45px rgba(26, 26, 26, 0.08)',
      },
    },
  },
  plugins: [],
}


/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Terminal-inspired palette with electric accents
        'void': '#0a0a0f',
        'abyss': '#12121a',
        'slate': '#1a1a24',
        'smoke': '#2a2a38',
        'ash': '#4a4a5a',
        'mist': '#8a8a9a',
        'cloud': '#cacad8',
        // Electric accents
        'volt': '#00ff88',
        'volt-dim': '#00cc6a',
        'pulse': '#ff3366',
        'pulse-dim': '#cc2952',
        'arc': '#00d4ff',
        'arc-dim': '#00a8cc',
        'spark': '#ffcc00',
        'spark-dim': '#cc9900',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'display': ['Space Grotesk', 'sans-serif'],
        'body': ['IBM Plex Sans', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 4s ease-in-out infinite',
        'flicker': 'flicker 0.15s infinite',
      },
      keyframes: {
        glow: {
          '0%': { opacity: '0.5', filter: 'blur(8px)' },
          '100%': { opacity: '1', filter: 'blur(12px)' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(-100%)' },
          '50%': { transform: 'translateY(100%)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [],
}

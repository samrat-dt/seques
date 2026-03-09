/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['"DM Serif Display"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'monospace'],
      },
      colors: {
        base: '#0d0d0f',
        surface: '#141416',
        raised: '#1c1c20',
        overlay: '#242428',
        accent: {
          DEFAULT: '#f59e0b',
          dim: '#92400e',
        },
        primary: '#f0ede8',
        secondary: '#9b9691',
        muted: '#5a5753',
        success: {
          bg: '#052e16',
          text: '#4ade80',
          border: '#166534',
        },
        warning: {
          bg: '#2d1a00',
          text: '#fbbf24',
          border: '#92400e',
        },
        danger: {
          bg: '#2d0a0a',
          text: '#f87171',
          border: '#991b1b',
        },
        info: {
          bg: '#0c1a2e',
          text: '#60a5fa',
          border: '#1e40af',
        },
      },
      borderColor: {
        subtle: 'rgba(255,255,255,0.06)',
        mid: 'rgba(255,255,255,0.12)',
        strong: 'rgba(255,255,255,0.20)',
      },
      borderWidth: {
        3: '3px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.5)',
        'card-hover': '0 4px 16px rgba(0,0,0,0.4)',
        'btn-primary':
          '0 0 0 1px rgba(245,158,11,0.3), 0 4px 12px rgba(245,158,11,0.15)',
        'input-focus': '0 0 0 2px rgba(245,158,11,0.25)',
        'glow-success': '0 0 0 1px rgba(74,222,128,0.2)',
      },
      animation: {
        'cursor-blink': 'blink 1s step-end infinite',
        'fade-in': 'fadeIn 150ms ease-out',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

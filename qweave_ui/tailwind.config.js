/** @type {import('tailwindcss').Config} */

module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Q-Weave Quantum Synthetic Design System
        background: '#0b1326',
        'on-background': '#e0e0e0',
        surface: {
          DEFAULT: '#0b1326',
          dim: '#0b1326',
          bright: '#31394d',
          variant: '#2d3449',
        },
        'surface-container': {
          lowest: '#060e20',
          low: '#131b2e',
          DEFAULT: '#171f33',
          high: '#222a3d',
          highest: '#2d3449',
        },
        primary: {
          DEFAULT: '#8aebff',
          fixed: '#a2eeff',
          dim: '#2fd9f4',
          container: '#22d3ee',
        },
        secondary: {
          DEFAULT: '#d0bcff',
          fixed: '#e9ddff',
          dim: '#d0bcff',
          container: '#571bc1',
        },
        tertiary: {
          DEFAULT: '#ffd6a3',
          fixed: '#ffddb5',
          dim: '#ffb957',
          container: '#ffb13b',
        },
        error: {
          DEFAULT: '#ffb4ab',
          container: '#93000a',
        },
        outline: {
          DEFAULT: '#859397',
          variant: '#3c494c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'data-lg': ['20px', { lineHeight: '28px', fontWeight: '500' }],
        'data-md': ['14px', { lineHeight: '20px', fontWeight: '500' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.1em', fontWeight: '700' }],
      },
      spacing: {
        unit: '4px',
        gutter: '24px',
        margin: '32px',
        'container-padding': '20px',
      },
      backdropBlur: {
        '2xl': '16px',
      },
    },
  },
  plugins: [],
};

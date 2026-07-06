/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Geist Variable"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"Geist Mono Variable"', "ui-monospace", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        sidebar: "hsl(var(--sidebar))",
        subtle: "hsl(var(--subtle))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        xs: "0 1px 2px 0 rgb(16 24 40 / 0.04)",
        sm: "0 1px 3px 0 rgb(16 24 40 / 0.06), 0 1px 2px -1px rgb(16 24 40 / 0.04)",
        md: "0 4px 12px -2px rgb(16 24 40 / 0.08), 0 2px 4px -2px rgb(16 24 40 / 0.04)",
        pop: "0 12px 32px -8px rgb(16 24 40 / 0.16)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        "flow-dash": { to: { strokeDashoffset: "-16" } },
      },
      animation: {
        "fade-up": "fade-up 0.4s cubic-bezier(0.22,1,0.36,1) both",
        "pulse-dot": "pulse-dot 1.6s ease-in-out infinite",
        "flow-dash": "flow-dash 0.8s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

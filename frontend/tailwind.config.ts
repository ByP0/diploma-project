import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

const channel = (name: string) => `rgb(var(${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: "16px",
        sm: "20px",
        lg: "24px",
        xl: "32px",
      },
      screens: {
        "2xl": "1440px",
      },
    },
    extend: {
      colors: {
        background: channel("--color-background"),
        foreground: channel("--color-foreground"),
        surface: channel("--color-surface"),
        "surface-raised": channel("--color-surface-raised"),
        muted: channel("--color-muted"),
        "muted-foreground": channel("--color-muted-foreground"),
        border: channel("--color-border"),
        "border-strong": channel("--color-border-strong"),
        ring: channel("--color-ring"),
        primary: {
          DEFAULT: channel("--color-primary"),
          foreground: channel("--color-primary-foreground"),
          hover: channel("--color-primary-hover"),
          active: channel("--color-primary-active"),
          soft: channel("--color-primary-soft"),
          border: channel("--color-primary-border"),
        },
        accent: {
          DEFAULT: channel("--color-accent"),
          foreground: channel("--color-accent-foreground"),
          soft: channel("--color-accent-soft"),
        },
        success: {
          DEFAULT: channel("--color-success"),
          foreground: channel("--color-success-foreground"),
          soft: channel("--color-success-soft"),
          border: channel("--color-success-border"),
        },
        warning: {
          DEFAULT: channel("--color-warning"),
          foreground: channel("--color-warning-foreground"),
          soft: channel("--color-warning-soft"),
          border: channel("--color-warning-border"),
        },
        danger: {
          DEFAULT: channel("--color-danger"),
          foreground: channel("--color-danger-foreground"),
          soft: channel("--color-danger-soft"),
          border: channel("--color-danger-border"),
        },
        info: {
          DEFAULT: channel("--color-info"),
          foreground: channel("--color-info-foreground"),
          soft: channel("--color-info-soft"),
          border: channel("--color-info-border"),
        },
        admin: {
          surface: channel("--color-admin-surface"),
          sidebar: channel("--color-admin-sidebar"),
          accent: channel("--color-admin-accent"),
          foreground: channel("--color-admin-foreground"),
        },
        skeleton: channel("--color-skeleton"),
        "skeleton-highlight": channel("--color-skeleton-highlight"),
      },
      fontFamily: {
        sans: ["Inter", "Roboto", "system-ui", ...defaultTheme.fontFamily.sans],
        display: ["Manrope", "Inter", "system-ui", ...defaultTheme.fontFamily.sans],
        mono: ["JetBrains Mono", ...defaultTheme.fontFamily.mono],
      },
      fontSize: {
        "display-lg": ["44px", { lineHeight: "52px", fontWeight: "750" }],
        "display-md": ["36px", { lineHeight: "44px", fontWeight: "750" }],
        h1: ["32px", { lineHeight: "40px", fontWeight: "720" }],
        h2: ["26px", { lineHeight: "34px", fontWeight: "700" }],
        h3: ["22px", { lineHeight: "30px", fontWeight: "700" }],
        h4: ["18px", { lineHeight: "26px", fontWeight: "650" }],
        body: ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        caption: ["12px", { lineHeight: "16px", fontWeight: "500" }],
        "button-sm": ["13px", { lineHeight: "18px", fontWeight: "650" }],
        button: ["14px", { lineHeight: "20px", fontWeight: "650" }],
        "button-lg": ["16px", { lineHeight: "22px", fontWeight: "700" }],
      },
      borderRadius: {
        xs: "4px",
        sm: "6px",
        md: "8px",
        lg: "8px",
        xl: "12px",
        "2xl": "16px",
      },
      boxShadow: {
        header: "0 1px 0 rgb(18 36 28 / 0.08), 0 8px 28px rgb(18 36 28 / 0.05)",
        card: "0 1px 2px rgb(18 36 28 / 0.06), 0 10px 32px rgb(18 36 28 / 0.06)",
        "card-hover": "0 8px 28px rgb(18 36 28 / 0.1)",
        modal: "0 20px 72px rgb(18 36 28 / 0.2)",
        "sticky-cart": "0 12px 36px rgb(18 36 28 / 0.14)",
        focus: "0 0 0 4px rgb(var(--color-ring) / 0.22)",
      },
      transitionTimingFunction: {
        product: "cubic-bezier(0.2, 0.7, 0.2, 1)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "modal-in": {
          from: { opacity: "0", transform: "translateY(8px) scale(0.98)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "toast-in": {
          from: { opacity: "0", transform: "translateX(16px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 160ms ease-out",
        "modal-in": "modal-in 180ms cubic-bezier(0.2, 0.7, 0.2, 1)",
        "toast-in": "toast-in 180ms cubic-bezier(0.2, 0.7, 0.2, 1)",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};

export default config;

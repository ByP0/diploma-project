export const themeTokens = {
  color: {
    background: "rgb(var(--color-background))",
    foreground: "rgb(var(--color-foreground))",
    surface: "rgb(var(--color-surface))",
    muted: "rgb(var(--color-muted))",
    primary: "rgb(var(--color-primary))",
    primaryHover: "rgb(var(--color-primary-hover))",
    accent: "rgb(var(--color-accent))",
    border: "rgb(var(--color-border))",
    danger: "rgb(var(--color-danger))",
    warning: "rgb(var(--color-warning))",
    success: "rgb(var(--color-success))",
    info: "rgb(var(--color-info))",
  },
  radius: {
    xs: "var(--radius-xs)",
    sm: "var(--radius-sm)",
    md: "var(--radius-md)",
    lg: "var(--radius-lg)",
    xl: "var(--radius-xl)",
  },
  shadow: {
    header: "var(--shadow-header)",
    card: "var(--shadow-card)",
    cardHover: "var(--shadow-card-hover)",
    modal: "var(--shadow-modal)",
    stickyCart: "var(--shadow-sticky-cart)",
  },
  typography: {
    sans: "var(--font-sans)",
    display: "var(--font-display)",
    mono: "var(--font-mono)",
  },
  zIndex: {
    header: "var(--z-header)",
    stickyCart: "var(--z-sticky-cart)",
    modal: "var(--z-modal)",
    toast: "var(--z-toast)",
  },
} as const;

export type ThemeTokens = typeof themeTokens;

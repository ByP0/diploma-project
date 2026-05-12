import { createElement, type HTMLAttributes, type ReactNode } from "react";
import { cx } from "@shared/lib/cx";

type HeadingLevel = "h1" | "h2" | "h3" | "h4";
type HeadingSize = "lg" | "md" | "sm" | "xl";

type HeadingProps = HTMLAttributes<HTMLHeadingElement> & {
  as?: HeadingLevel;
  children: ReactNode;
  size?: HeadingSize;
};

export function Heading({ as = "h2", children, className, size = "md", ...props }: HeadingProps) {
  return createElement(as, { className: cx("ds-heading", `ds-heading--${size}`, className), ...props }, children);
}

type TextTone = "default" | "muted" | "strong";

type TextProps = HTMLAttributes<HTMLParagraphElement> & {
  children: ReactNode;
  tone?: TextTone;
};

export function Text({ children, className, tone = "default", ...props }: TextProps) {
  return (
    <p className={cx("ds-text", `ds-text--${tone}`, className)} {...props}>
      {children}
    </p>
  );
}

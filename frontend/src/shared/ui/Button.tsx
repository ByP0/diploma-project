import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "@shared/lib/cx";

type ButtonVariant = "danger" | "ghost" | "primary" | "secondary";
type ButtonSize = "md" | "sm";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  isLoading?: boolean;
  leftSlot?: ReactNode;
  size?: ButtonSize;
  variant?: ButtonVariant;
};

export function Button({
  children,
  className,
  disabled,
  isLoading = false,
  leftSlot,
  size = "md",
  type = "button",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cx("ds-button", `ds-button--${variant}`, `ds-button--${size}`, isLoading && "is-loading", className)}
      disabled={disabled || isLoading}
      type={type}
      {...props}
    >
      {isLoading ? <span className="ds-button__spinner" aria-hidden="true" /> : leftSlot}
      <span>{children}</span>
    </button>
  );
}

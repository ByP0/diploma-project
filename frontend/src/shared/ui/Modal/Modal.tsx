import * as React from "react";
import { createPortal } from "react-dom";

import { cn } from "../../lib/cn";

const sizeClass = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-3xl",
  xl: "max-w-5xl",
  full: "max-w-[calc(100vw-32px)]",
} as const;

export type ModalSize = keyof typeof sizeClass;

export interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  size?: ModalSize;
  className?: string;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  labelledBy?: string;
  describedBy?: string;
}

export function Modal({
  open,
  onOpenChange,
  children,
  size = "md",
  className,
  closeOnEscape = true,
  closeOnOverlayClick = true,
  labelledBy,
  describedBy,
}: ModalProps) {
  React.useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && closeOnEscape) {
        onOpenChange(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [closeOnEscape, onOpenChange, open]);

  if (!open || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[var(--z-modal)] grid place-items-center bg-foreground/[0.35] px-4 py-6 backdrop-blur-sm animate-fade-in"
      onMouseDown={() => {
        if (closeOnOverlayClick) {
          onOpenChange(false);
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        className={cn(
          "max-h-[calc(100vh-48px)] w-full overflow-hidden rounded-lg border border-border bg-surface shadow-modal animate-modal-in",
          sizeClass[size],
          className,
        )}
        onMouseDown={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}

export function ModalHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("border-b border-border px-5 py-4", className)} {...props} />;
}

export function ModalTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-h3 text-foreground", className)} {...props} />;
}

export function ModalDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("mt-1 text-body-sm text-muted-foreground", className)} {...props} />;
}

export function ModalBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("max-h-[70vh] overflow-y-auto px-5 py-5 scrollbar-soft", className)} {...props} />;
}

export function ModalFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col-reverse gap-3 border-t border-border px-5 py-4 sm:flex-row sm:justify-end", className)}
      {...props}
    />
  );
}

export function ModalClose({
  className,
  children = "x",
  onClick,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      aria-label={props["aria-label"] ?? "Close modal"}
      className={cn(
        "focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground",
        className,
      )}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}

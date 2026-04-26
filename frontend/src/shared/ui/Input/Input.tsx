import * as React from "react";

import { cn } from "../../lib/cn";

const inputVariantClass = {
  default: "border-border bg-surface text-foreground placeholder:text-muted-foreground",
  search: "border-border-strong bg-white text-foreground placeholder:text-muted-foreground shadow-sm",
  quiet: "border-transparent bg-muted text-foreground placeholder:text-muted-foreground",
  admin: "border-border bg-surface-raised text-foreground placeholder:text-muted-foreground",
  invalid: "border-danger bg-danger-soft text-foreground placeholder:text-danger/70",
} as const;

const inputSizeClass = {
  sm: "min-h-[var(--control-height-sm)] px-3 text-body-sm",
  md: "min-h-[var(--control-height-md)] px-3.5 text-body-sm",
  lg: "min-h-[var(--control-height-lg)] px-4 text-body",
} as const;

export type InputVariant = keyof typeof inputVariantClass;
export type InputSize = keyof typeof inputSizeClass;

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  variant?: InputVariant;
  inputSize?: InputSize;
  leftSlot?: React.ReactNode;
  rightSlot?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = "default",
      inputSize = "md",
      leftSlot,
      rightSlot,
      "aria-invalid": ariaInvalid,
      ...props
    },
    ref,
  ) => {
    const resolvedVariant = ariaInvalid ? "invalid" : variant;
    const input = (
      <input
        ref={ref}
        aria-invalid={ariaInvalid}
        className={cn(
          "focus-ring w-full rounded-md border transition duration-150 ease-product disabled:cursor-not-allowed disabled:opacity-60",
          inputVariantClass[resolvedVariant],
          inputSizeClass[inputSize],
          leftSlot && "pl-10",
          rightSlot && "pr-10",
          className,
        )}
        {...props}
      />
    );

    if (!leftSlot && !rightSlot) {
      return input;
    }

    return (
      <span className="relative block w-full">
        {leftSlot ? (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
            {leftSlot}
          </span>
        ) : null}
        {input}
        {rightSlot ? (
          <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground">{rightSlot}</span>
        ) : null}
      </span>
    );
  },
);

Input.displayName = "Input";

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  variant?: InputVariant;
  inputSize?: InputSize;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, variant = "default", inputSize = "md", "aria-invalid": ariaInvalid, ...props }, ref) => {
    const resolvedVariant = ariaInvalid ? "invalid" : variant;

    return (
      <select
        ref={ref}
        aria-invalid={ariaInvalid}
        className={cn(
          "focus-ring w-full rounded-md border transition duration-150 ease-product disabled:cursor-not-allowed disabled:opacity-60",
          inputVariantClass[resolvedVariant],
          inputSizeClass[inputSize],
          className,
        )}
        {...props}
      />
    );
  },
);

Select.displayName = "Select";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: InputVariant;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant = "default", "aria-invalid": ariaInvalid, ...props }, ref) => {
    const resolvedVariant = ariaInvalid ? "invalid" : variant;

    return (
      <textarea
        ref={ref}
        aria-invalid={ariaInvalid}
        className={cn(
          "focus-ring min-h-[112px] w-full resize-y rounded-md border px-3.5 py-3 text-body-sm transition duration-150 ease-product disabled:cursor-not-allowed disabled:opacity-60",
          inputVariantClass[resolvedVariant],
          className,
        )}
        {...props}
      />
    );
  },
);

Textarea.displayName = "Textarea";

export interface FieldProps extends React.HTMLAttributes<HTMLDivElement> {
  invalid?: boolean;
}

export function Field({ className, invalid, ...props }: FieldProps) {
  return <div className={cn("grid gap-1.5", invalid && "text-danger", className)} {...props} />;
}

export function FieldLabel({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("text-body-sm font-semibold text-foreground", className)} {...props} />;
}

export function FieldHint({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-caption text-muted-foreground", className)} {...props} />;
}

export function FieldError({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p role="alert" className={cn("text-caption font-semibold text-danger", className)} {...props} />;
}

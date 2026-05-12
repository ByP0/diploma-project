import { useId, type InputHTMLAttributes } from "react";
import { cx } from "@shared/lib/cx";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  error?: string;
  hint?: string;
  label: string;
};

export function TextField({ className, error, hint, id, label, ...props }: TextFieldProps) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <label className={cx("ds-field", className)} htmlFor={inputId}>
      <span className="ds-field__label">{label}</span>
      <input
        aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
        aria-invalid={Boolean(error)}
        className="ds-input"
        id={inputId}
        {...props}
      />
      {hint ? (
        <span className="ds-field__hint" id={hintId}>
          {hint}
        </span>
      ) : null}
      {error ? (
        <span className="ds-field__error" id={errorId}>
          {error}
        </span>
      ) : null}
    </label>
  );
}

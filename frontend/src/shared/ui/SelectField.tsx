import { useId, type SelectHTMLAttributes } from "react";
import { cx } from "@shared/lib/cx";

type SelectOption<TValue extends string> = {
  label: string;
  value: TValue;
};

type SelectFieldProps<TValue extends string> = Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> & {
  error?: string;
  hint?: string;
  label: string;
  options: SelectOption<TValue>[];
};

export function SelectField<TValue extends string>({
  className,
  error,
  hint,
  id,
  label,
  options,
  ...props
}: SelectFieldProps<TValue>) {
  const generatedId = useId();
  const selectId = id || generatedId;
  const hintId = hint ? `${selectId}-hint` : undefined;
  const errorId = error ? `${selectId}-error` : undefined;

  return (
    <label className={cx("ds-field", className)} htmlFor={selectId}>
      <span className="ds-field__label">{label}</span>
      <select
        aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
        aria-invalid={Boolean(error)}
        className="ds-input ds-select"
        id={selectId}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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

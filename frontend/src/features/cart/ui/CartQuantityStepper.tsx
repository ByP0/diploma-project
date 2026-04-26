import { cn } from "../../../shared/lib/cn";

export interface CartQuantityStepperProps {
  value: number;
  max: number;
  disabled?: boolean;
  onChange: (value: number) => void;
  className?: string;
}

export function CartQuantityStepper({ value, max, disabled, onChange, className }: CartQuantityStepperProps) {
  return (
    <div className={cn("inline-grid w-[132px] grid-cols-[38px_minmax(0,1fr)_38px] overflow-hidden rounded-md border border-border bg-surface", className)}>
      <button
        aria-label="Уменьшить количество"
        className="focus-ring min-h-[38px] border-r border-border font-black text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
        disabled={disabled || value <= 1}
        onClick={() => onChange(value - 1)}
        type="button"
      >
        -
      </button>
      <input
        aria-label="Количество"
        className="min-w-0 border-0 bg-transparent text-center text-body-sm font-bold text-foreground focus:outline-none disabled:opacity-60"
        disabled={disabled}
        max={max}
        min={1}
        onChange={(event) => onChange(Number(event.target.value) || 1)}
        type="number"
        value={value}
      />
      <button
        aria-label="Увеличить количество"
        className="focus-ring min-h-[38px] border-l border-border font-black text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
        disabled={disabled || value >= max}
        onClick={() => onChange(value + 1)}
        type="button"
      >
        +
      </button>
    </div>
  );
}

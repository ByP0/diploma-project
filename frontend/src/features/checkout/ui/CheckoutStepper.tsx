import { cn } from "../../../shared/lib/cn";
import { checkoutSteps, type CheckoutStepId } from "../model";

export interface CheckoutStepperProps {
  activeStep: CheckoutStepId;
  completedSteps?: CheckoutStepId[];
  onStepSelect?: (step: CheckoutStepId) => void;
}

export function CheckoutStepper({ activeStep, completedSteps = [], onStepSelect }: CheckoutStepperProps) {
  const activeIndex = checkoutSteps.findIndex((step) => step.id === activeStep);

  return (
    <nav aria-label="Шаги оформления" className="overflow-x-auto scrollbar-soft">
      <ol className="grid min-w-[720px] grid-cols-5 gap-2">
        {checkoutSteps.map((step, index) => {
          const isActive = step.id === activeStep;
          const isCompleted = completedSteps.includes(step.id) || index < activeIndex;
          const canSelect = Boolean(onStepSelect && (isCompleted || index <= activeIndex));

          return (
            <li key={step.id}>
              <button
                className={cn(
                  "focus-ring grid w-full gap-1 rounded-lg border px-3 py-3 text-left transition duration-200 ease-product",
                  isActive && "border-primary bg-primary text-primary-foreground shadow-sm",
                  !isActive && isCompleted && "border-success-border bg-success-soft text-success",
                  !isActive && !isCompleted && "border-border bg-surface text-muted-foreground",
                  canSelect && !isActive && "hover:border-primary-border hover:bg-primary-soft hover:text-primary-active",
                )}
                disabled={!canSelect}
                onClick={() => onStepSelect?.(step.id)}
                type="button"
              >
                <span className="flex items-center gap-2">
                  <span
                    className={cn(
                      "grid h-7 w-7 place-items-center rounded-md border text-caption font-black",
                      isActive && "border-white/40 bg-white/15",
                      !isActive && isCompleted && "border-success-border bg-surface",
                      !isActive && !isCompleted && "border-border bg-muted",
                    )}
                  >
                    {isCompleted ? "✓" : index + 1}
                  </span>
                  <span className="text-body-sm font-black">{step.title}</span>
                </span>
                <span className={cn("text-caption", isActive ? "text-primary-foreground/80" : "text-muted-foreground")}>
                  {step.description}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

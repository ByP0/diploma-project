import * as React from "react";

import { cn } from "../../lib/cn";

export type ToastVariant = "success" | "warning" | "danger" | "info" | "neutral";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: React.ReactNode;
}

export interface ToastInput extends Omit<ToastMessage, "id"> {
  id?: string;
}

interface ToastContextValue {
  toasts: ToastMessage[];
  toast: (message: ToastInput) => string;
  dismiss: (id: string) => void;
  clear: () => void;
}

type ToastAction =
  | { type: "add"; toast: ToastMessage }
  | { type: "dismiss"; id: string }
  | { type: "clear" };

const ToastContext = React.createContext<ToastContextValue | null>(null);

function reducer(state: ToastMessage[], action: ToastAction): ToastMessage[] {
  switch (action.type) {
    case "add":
      return [action.toast, ...state].slice(0, 6);
    case "dismiss":
      return state.filter((toast) => toast.id !== action.id);
    case "clear":
      return [];
    default:
      return state;
  }
}

function createToastId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, dispatch] = React.useReducer(reducer, []);
  const timers = React.useRef(new Map<string, ReturnType<typeof globalThis.setTimeout>>());

  const dismiss = React.useCallback((id: string) => {
    const timer = timers.current.get(id);
    if (timer) {
      globalThis.clearTimeout(timer);
      timers.current.delete(id);
    }
    dispatch({ type: "dismiss", id });
  }, []);

  const scheduleDismiss = React.useCallback(
    (id: string, duration = 5000) => {
      if (duration === Infinity) {
        return;
      }

      const timer = globalThis.setTimeout(() => dismiss(id), duration);
      timers.current.set(id, timer);
    },
    [dismiss],
  );

  const toast = React.useCallback(
    (message: ToastInput) => {
      const id = message.id ?? createToastId();
      dispatch({
        type: "add",
        toast: {
          id,
          variant: "neutral",
          duration: 5000,
          ...message,
        },
      });
      scheduleDismiss(id, message.duration);
      return id;
    },
    [scheduleDismiss],
  );

  const clear = React.useCallback(() => {
    timers.current.forEach((timer) => globalThis.clearTimeout(timer));
    timers.current.clear();
    dispatch({ type: "clear" });
  }, []);

  React.useEffect(
    () => () => {
      timers.current.forEach((timer) => globalThis.clearTimeout(timer));
      timers.current.clear();
    },
    [],
  );

  const value = React.useMemo(() => ({ toasts, toast, dismiss, clear }), [clear, dismiss, toast, toasts]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

const toastVariantClass = {
  success: "border-success-border bg-success-soft text-success",
  warning: "border-warning-border bg-warning-soft text-warning",
  danger: "border-danger-border bg-danger-soft text-danger",
  info: "border-info-border bg-info-soft text-info",
  neutral: "border-border bg-surface text-foreground",
} as const;

export interface ToastProps extends ToastMessage {
  onDismiss?: (id: string) => void;
}

export function Toast({ id, title, description, variant = "neutral", action, onDismiss }: ToastProps) {
  return (
    <div
      role="status"
      className={cn(
        "pointer-events-auto grid w-full gap-2 rounded-lg border p-4 shadow-card animate-toast-in",
        toastVariantClass[variant],
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-body-sm font-bold text-foreground">{title}</p>
          {description ? <p className="mt-1 text-body-sm text-muted-foreground">{description}</p> : null}
        </div>
        <button
          type="button"
          aria-label="Close notification"
          className="focus-ring inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-white/70 hover:text-foreground"
          onClick={() => onDismiss?.(id)}
        >
          x
        </button>
      </div>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}

export function ToastViewport({
  toasts,
  onDismiss,
}: {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}) {
  if (!toasts.length) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[var(--z-toast)] grid w-[min(420px,calc(100vw-32px))] gap-3">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

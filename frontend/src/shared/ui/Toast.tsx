import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { cx } from "@shared/lib/cx";

type ToastVariant = "error" | "info" | "success" | "warning";

type Toast = {
  description?: string;
  id: string;
  title: string;
  variant: ToastVariant;
};

type ShowToastInput = {
  description?: string;
  title: string;
  variant?: ToastVariant;
};

type ToastContextValue = {
  dismissToast: (id: string) => void;
  showToast: (toast: ShowToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function createToastId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

type ToastProviderProps = {
  children: ReactNode;
};

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((currentToasts) => currentToasts.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((toast: ShowToastInput) => {
    setToasts((currentToasts) => [
      ...currentToasts.slice(-3),
      {
        id: createToastId(),
        variant: toast.variant || "info",
        title: toast.title,
        description: toast.description,
      },
    ]);
  }, []);

  const value = useMemo(() => ({ dismissToast, showToast }), [dismissToast, showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport dismissToast={dismissToast} toasts={toasts} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }

  return context;
}

type ToastViewportProps = {
  dismissToast: (id: string) => void;
  toasts: Toast[];
};

function ToastViewport({ dismissToast, toasts }: ToastViewportProps) {
  return (
    <div aria-live="polite" aria-relevant="additions" className="ds-toast-viewport">
      {toasts.map((toast) => (
        <ToastItem dismissToast={dismissToast} key={toast.id} toast={toast} />
      ))}
    </div>
  );
}

type ToastItemProps = {
  dismissToast: (id: string) => void;
  toast: Toast;
};

function ToastItem({ dismissToast, toast }: ToastItemProps) {
  useEffect(() => {
    const timeoutId = window.setTimeout(() => dismissToast(toast.id), 4200);
    return () => window.clearTimeout(timeoutId);
  }, [dismissToast, toast.id]);

  return (
    <section className={cx("ds-toast", `ds-toast--${toast.variant}`)}>
      <div>
        <strong>{toast.title}</strong>
        {toast.description ? <p>{toast.description}</p> : null}
      </div>
      <button aria-label="Dismiss notification" onClick={() => dismissToast(toast.id)} type="button">
        x
      </button>
    </section>
  );
}

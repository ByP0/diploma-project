import { useEffect, type ReactNode } from "react";
import { Button } from "./Button";

type ModalProps = {
  children: ReactNode;
  footer?: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  title: string;
};

export function Modal({ children, footer, isOpen, onClose, title }: ModalProps) {
  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="ds-modal-backdrop" role="presentation">
      <section aria-label={title} aria-modal="true" className="ds-modal" role="dialog">
        <header className="ds-modal__header">
          <h2>{title}</h2>
          <Button aria-label="Close modal" onClick={onClose} size="sm" variant="ghost">
            Close
          </Button>
        </header>
        <div className="ds-modal__body">{children}</div>
        {footer ? <footer className="ds-modal__footer">{footer}</footer> : null}
      </section>
    </div>
  );
}

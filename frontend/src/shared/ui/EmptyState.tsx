import type { ReactNode } from "react";

type EmptyStateProps = {
  action?: ReactNode;
  description?: string;
  title: string;
};

export function EmptyState({ action, description, title }: EmptyStateProps) {
  return (
    <section className="ds-state ds-state--empty">
      <span className="ds-state__mark" aria-hidden="true">
        -
      </span>
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
      {action ? <div className="ds-state__action">{action}</div> : null}
    </section>
  );
}

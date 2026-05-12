import type { ReactNode } from "react";

type ErrorStateProps = {
  action?: ReactNode;
  description?: string;
  title?: string;
};

export function ErrorState({
  action,
  description = "Something went wrong. Try again or check the service status.",
  title = "Unable to load data",
}: ErrorStateProps) {
  return (
    <section className="ds-state ds-state--error" role="alert">
      <span className="ds-state__mark" aria-hidden="true">
        !
      </span>
      <h2>{title}</h2>
      <p>{description}</p>
      {action ? <div className="ds-state__action">{action}</div> : null}
    </section>
  );
}

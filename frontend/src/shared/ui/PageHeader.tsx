import type { ReactNode } from "react";
import "./page-header.css";

type PageHeaderProps = {
  actions?: ReactNode;
  description?: string;
  eyebrow?: string;
  title: string;
};

export function PageHeader({ actions, description, eyebrow, title }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        {eyebrow ? <p className="page-eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p className="page-description">{description}</p> : null}
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </header>
  );
}

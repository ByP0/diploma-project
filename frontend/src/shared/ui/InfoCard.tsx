import type { ReactNode } from "react";

type InfoCardProps = {
  label: string;
  value: ReactNode;
};

export function InfoCard({ label, value }: InfoCardProps) {
  return (
    <article className="surface-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

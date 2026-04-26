import * as React from "react";

import { cn } from "../../lib/cn";
import { Badge, type BadgeVariant } from "../Badge";

export interface AdminStatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string;
  description?: string;
  trend?: string;
  trendVariant?: BadgeVariant;
}

export function AdminStatCard({
  title,
  value,
  description,
  trend,
  trendVariant = "primary",
  className,
  ...props
}: AdminStatCardProps) {
  return (
    <section className={cn("admin-kpi-card", className)} {...props}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-caption font-bold uppercase text-muted-foreground">{title}</p>
          <p className="mt-2 text-display-md font-bold tracking-normal text-foreground">{value}</p>
        </div>
        {trend ? <Badge variant={trendVariant}>{trend}</Badge> : null}
      </div>
      {description ? <p className="mt-3 text-body-sm text-muted-foreground">{description}</p> : null}
    </section>
  );
}

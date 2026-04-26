import * as React from "react";

import { cn } from "../../lib/cn";

const cardVariantClass = {
  surface: "border-border bg-surface shadow-sm",
  elevated: "border-border bg-surface shadow-card",
  product: "border-border bg-surface shadow-sm hover:border-primary-border hover:shadow-card-hover",
  checkout: "border-border bg-surface shadow-sm",
  admin: "border-border bg-surface shadow-sm",
  muted: "border-border bg-surface-raised shadow-none",
  bare: "border-transparent bg-transparent shadow-none",
} as const;

export type CardVariant = keyof typeof cardVariantClass;

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  interactive?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "surface", interactive = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border",
        cardVariantClass[variant],
        interactive && "transition duration-200 ease-product hover:-translate-y-0.5",
        className,
      )}
      {...props}
    />
  ),
);

Card.displayName = "Card";

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-1.5 border-b border-border px-5 py-4", className)} {...props} />
  ),
);

CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("text-h4 text-foreground", className)} {...props} />
  ),
);

CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-body-sm text-muted-foreground", className)} {...props} />
  ),
);

CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("p-5", className)} {...props} />,
);

CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center gap-3 border-t border-border px-5 py-4", className)} {...props} />
  ),
);

CardFooter.displayName = "CardFooter";

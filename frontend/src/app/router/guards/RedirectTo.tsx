import * as React from "react";

export interface RedirectToProps {
  href: string;
  replace?: boolean;
}

export function RedirectTo({ href, replace = true }: RedirectToProps) {
  React.useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (replace) {
      window.location.replace(href);
      return;
    }

    window.location.assign(href);
  }, [href, replace]);

  return (
    <a className="text-primary" href={href}>
      Перейти
    </a>
  );
}

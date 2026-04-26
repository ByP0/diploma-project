import type { StorefrontLinkComponent, StorefrontLinkProps } from "./types";

export function DefaultStorefrontLink({ href, children, ...props }: StorefrontLinkProps) {
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
}

export function resolveLinkComponent(LinkComponent?: StorefrontLinkComponent): StorefrontLinkComponent {
  return LinkComponent ?? DefaultStorefrontLink;
}

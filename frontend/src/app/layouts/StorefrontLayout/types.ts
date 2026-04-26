import type * as React from "react";

export interface NavigationItem {
  label: string;
  href: string;
  count?: number;
  badge?: string;
  active?: boolean;
  children?: NavigationItem[];
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface StorefrontUserSummary {
  name?: string;
  email?: string;
  isAuthenticated?: boolean;
}

export interface StorefrontCounters {
  favoriteItems?: number;
  cartItems?: number;
  orderItems?: number;
  cartTotal?: string;
}

export interface StorefrontLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
}

export type StorefrontLinkComponent = React.ComponentType<StorefrontLinkProps>;

export interface FooterColumn {
  title: string;
  links: NavigationItem[];
}

export interface SocialLink {
  label: string;
  href: string;
}

export interface StorefrontNavigationData {
  breadcrumbs: BreadcrumbItem[];
  quickCategories: NavigationItem[];
  catalogCategories: NavigationItem[];
  brands: NavigationItem[];
  farmerLinks: NavigationItem[];
  newLinks: NavigationItem[];
  footerColumns: FooterColumn[];
  socialLinks: SocialLink[];
}

export interface StorefrontLayoutProps {
  children: React.ReactNode;
  navigation?: Partial<StorefrontNavigationData>;
  user?: StorefrontUserSummary;
  counters?: StorefrontCounters;
  searchQuery?: string;
  defaultSearchQuery?: string;
  onSearchQueryChange?: (query: string) => void;
  onSearchSubmit?: (query: string) => void;
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

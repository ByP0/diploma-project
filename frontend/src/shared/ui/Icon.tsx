import type { ReactNode, SVGProps } from "react";

type IconName =
  | "arrow-left"
  | "arrow-right"
  | "cart"
  | "catalog"
  | "chevron-down"
  | "close"
  | "credit-card"
  | "home"
  | "logout"
  | "message"
  | "minus"
  | "package"
  | "plus"
  | "search"
  | "send"
  | "star"
  | "trash"
  | "user";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
  size?: number;
};

const icons: Record<IconName, ReactNode> = {
  "arrow-left": (
    <>
      <path d="m12 19-7-7 7-7" />
      <path d="M19 12H5" />
    </>
  ),
  "arrow-right": (
    <>
      <path d="m12 5 7 7-7 7" />
      <path d="M5 12h14" />
    </>
  ),
  cart: (
    <>
      <path d="M6 6h15l-1.7 8.4a2 2 0 0 1-2 1.6H9.2a2 2 0 0 1-2-1.7L6 6Z" />
      <path d="M6 6 5.2 3H2" />
      <path d="M9 20h.01" />
      <path d="M18 20h.01" />
    </>
  ),
  catalog: (
    <>
      <path d="M4 4h7v7H4z" />
      <path d="M13 4h7v7h-7z" />
      <path d="M4 13h7v7H4z" />
      <path d="M13 13h7v7h-7z" />
    </>
  ),
  "chevron-down": <path d="m6 9 6 6 6-6" />,
  close: (
    <>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </>
  ),
  "credit-card": (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 10h18" />
      <path d="M7 15h3" />
    </>
  ),
  home: (
    <>
      <path d="m3 11 9-8 9 8" />
      <path d="M5 10v10h14V10" />
      <path d="M9 20v-6h6v6" />
    </>
  ),
  logout: (
    <>
      <path d="M10 17 15 12l-5-5" />
      <path d="M15 12H3" />
      <path d="M21 3v18" />
    </>
  ),
  message: (
    <>
      <path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-7a8 8 0 1 1 18-4Z" />
      <path d="M8 12h.01" />
      <path d="M12 12h.01" />
      <path d="M16 12h.01" />
    </>
  ),
  minus: <path d="M5 12h14" />,
  package: (
    <>
      <path d="m21 8-9-5-9 5 9 5 9-5Z" />
      <path d="M3 8v8l9 5 9-5V8" />
      <path d="M12 13v8" />
    </>
  ),
  plus: (
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  send: (
    <>
      <path d="m22 2-7 20-4-9-9-4 20-7Z" />
      <path d="M22 2 11 13" />
    </>
  ),
  star: (
    <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z" />
  ),
  trash: (
    <>
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="m19 6-1 15H6L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
};

export function Icon({ name, size = 20, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width={size}
      {...props}
    >
      {icons[name]}
    </svg>
  );
}

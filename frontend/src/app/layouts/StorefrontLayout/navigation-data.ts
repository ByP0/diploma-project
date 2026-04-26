import type { StorefrontNavigationData } from "./types";

export const defaultStorefrontNavigation: StorefrontNavigationData = {
  breadcrumbs: [{ label: "Главная", href: "/" }],
  quickCategories: [
    { label: "Овощи и фрукты", href: "/catalog/vegetables-fruits" },
    { label: "Молоко и яйца", href: "/catalog/dairy-eggs" },
    { label: "Мясо и рыба", href: "/catalog/meat-fish" },
    { label: "Кулинария", href: "/catalog/cooking" },
    { label: "Напитки", href: "/catalog/drinks" },
    { label: "Для детей", href: "/catalog/kids" },
  ],
  catalogCategories: [
    { label: "Овощи, фрукты, ягоды", href: "/catalog/vegetables-fruits", count: 482, active: true },
    { label: "Молочные продукты и яйца", href: "/catalog/dairy-eggs", count: 318 },
    { label: "Мясо, птица, рыба", href: "/catalog/meat-fish", count: 251 },
    { label: "Хлеб, выпечка, десерты", href: "/catalog/bakery", count: 176 },
    { label: "Сыры и деликатесы", href: "/catalog/cheese-delicacy", count: 143 },
    { label: "Бакалея и консервы", href: "/catalog/grocery", count: 392 },
    { label: "Заморозка", href: "/catalog/frozen", count: 204 },
    { label: "Напитки", href: "/catalog/drinks", count: 267 },
    { label: "Товары для дома", href: "/catalog/home", count: 119 },
  ],
  brands: [
    { label: "Ферма Эко", href: "/brands/ferma-eco" },
    { label: "Зеленая линия", href: "/brands/green-line" },
    { label: "Молочный двор", href: "/brands/milk-yard" },
    { label: "Северная рыба", href: "/brands/north-fish" },
  ],
  farmerLinks: [
    { label: "Фермерское молоко", href: "/catalog/farm/dairy" },
    { label: "Сезонные овощи", href: "/catalog/farm/vegetables" },
    { label: "Домашняя выпечка", href: "/catalog/farm/bakery" },
    { label: "Мед и варенье", href: "/catalog/farm/honey-jam" },
  ],
  newLinks: [
    { label: "Новинки недели", href: "/catalog/new", badge: "new" },
    { label: "Готовые наборы", href: "/catalog/sets" },
    { label: "Premium selection", href: "/catalog/premium" },
    { label: "Товары со скидкой", href: "/promotions", badge: "sale" },
  ],
  footerColumns: [
    {
      title: "Контакты",
      links: [
        { label: "+7 800 250-10-10", href: "tel:+78002501010" },
        { label: "help@grocery-market.ru", href: "mailto:help@grocery-market.ru" },
        { label: "Магазины и пункты выдачи", href: "/stores" },
      ],
    },
    {
      title: "Доставка",
      links: [
        { label: "Условия доставки", href: "/delivery" },
        { label: "Зоны и интервалы", href: "/delivery/zones" },
        { label: "Самовывоз", href: "/pickup" },
      ],
    },
    {
      title: "Оплата",
      links: [
        { label: "Способы оплаты", href: "/payment" },
        { label: "Возвраты", href: "/refunds" },
        { label: "Подарочные карты", href: "/gift-cards" },
      ],
    },
    {
      title: "Политика",
      links: [
        { label: "Пользовательское соглашение", href: "/legal/terms" },
        { label: "Политика конфиденциальности", href: "/legal/privacy" },
        { label: "Обработка персональных данных", href: "/legal/personal-data" },
      ],
    },
  ],
  socialLinks: [
    { label: "VK", href: "https://vk.com" },
    { label: "Telegram", href: "https://t.me" },
    { label: "YouTube", href: "https://youtube.com" },
  ],
};

export function mergeNavigationData(
  overrides: Partial<StorefrontNavigationData> | undefined,
): StorefrontNavigationData {
  return {
    ...defaultStorefrontNavigation,
    ...overrides,
  };
}

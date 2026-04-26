export interface HomeCategory {
  id: string;
  title: string;
  href: string;
  imageUrl: string;
  itemCount: number;
  tone: "primary" | "accent" | "success" | "info";
}

export interface HomeProduct {
  id: string;
  title: string;
  href: string;
  imageUrl: string;
  category: string;
  price: string;
  oldPrice?: string;
  unit: string;
  rating: string;
  badge?: string;
  badgeVariant?: "primary" | "accent" | "success" | "warning" | "danger" | "info";
}

export interface HomeBrand {
  id: string;
  title: string;
  href: string;
  imageUrl: string;
  description: string;
  badge?: string;
}

export interface HomeBenefit {
  id: string;
  title: string;
  description: string;
}

export interface HomePromoTile {
  id: string;
  title: string;
  description: string;
  href: string;
  imageUrl: string;
  cta: string;
  variant: "large" | "small";
}

export const homePromos: HomePromoTile[] = [
  {
    id: "fresh-week",
    title: "Свежая неделя",
    description: "Фрукты, зелень и молочные продукты с утренних поставок.",
    href: "/promotions/fresh-week",
    imageUrl: "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=80",
    cta: "Смотреть акции",
    variant: "large",
  },
  {
    id: "express",
    title: "Экспресс-доставка",
    description: "Привезём продукты к удобному интервалу.",
    href: "/delivery/express",
    imageUrl: "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?auto=format&fit=crop&w=700&q=80",
    cta: "Выбрать время",
    variant: "small",
  },
  {
    id: "farmers",
    title: "Фермерская полка",
    description: "Небольшие хозяйства, сезонные партии.",
    href: "/catalog/farm",
    imageUrl: "https://images.unsplash.com/photo-1523741543316-beb7fc7023d8?auto=format&fit=crop&w=700&q=80",
    cta: "Перейти",
    variant: "small",
  },
];

export const popularCategories: HomeCategory[] = [
  {
    id: "fruits",
    title: "Овощи и фрукты",
    href: "/catalog/vegetables-fruits",
    imageUrl: "https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=600&q=80",
    itemCount: 482,
    tone: "primary",
  },
  {
    id: "dairy",
    title: "Молоко и яйца",
    href: "/catalog/dairy-eggs",
    imageUrl: "https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=600&q=80",
    itemCount: 318,
    tone: "success",
  },
  {
    id: "meat",
    title: "Мясо и рыба",
    href: "/catalog/meat-fish",
    imageUrl: "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=600&q=80",
    itemCount: 251,
    tone: "accent",
  },
  {
    id: "bakery",
    title: "Хлеб и выпечка",
    href: "/catalog/bakery",
    imageUrl: "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80",
    itemCount: 176,
    tone: "info",
  },
  {
    id: "ready",
    title: "Кулинария",
    href: "/catalog/cooking",
    imageUrl: "https://images.unsplash.com/photo-1543353071-10c8ba85a904?auto=format&fit=crop&w=600&q=80",
    itemCount: 143,
    tone: "primary",
  },
  {
    id: "drinks",
    title: "Напитки",
    href: "/catalog/drinks",
    imageUrl: "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=600&q=80",
    itemCount: 267,
    tone: "success",
  },
];

export const dayProducts: HomeProduct[] = [
  {
    id: "banana",
    title: "Бананы органические",
    href: "/products/banana-organic",
    imageUrl: "https://images.unsplash.com/photo-1603833665858-e61d17a86224?auto=format&fit=crop&w=600&q=80",
    category: "Фрукты",
    price: "129 ₽",
    oldPrice: "169 ₽",
    unit: "кг",
    rating: "4.9",
    badge: "-24%",
    badgeVariant: "accent",
  },
  {
    id: "milk",
    title: "Молоко фермерское 3,5%",
    href: "/products/farm-milk",
    imageUrl: "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=600&q=80",
    category: "Молочные",
    price: "98 ₽",
    oldPrice: "119 ₽",
    unit: "900 мл",
    rating: "4.8",
    badge: "хит",
    badgeVariant: "primary",
  },
  {
    id: "salmon",
    title: "Филе лосося охлаждённое",
    href: "/products/salmon-filet",
    imageUrl: "https://images.unsplash.com/photo-1580476262798-bddd9f4b7369?auto=format&fit=crop&w=600&q=80",
    category: "Рыба",
    price: "749 ₽",
    oldPrice: "899 ₽",
    unit: "300 г",
    rating: "4.7",
    badge: "день",
    badgeVariant: "warning",
  },
  {
    id: "avocado",
    title: "Авокадо Hass спелое",
    href: "/products/avocado-hass",
    imageUrl: "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?auto=format&fit=crop&w=600&q=80",
    category: "Овощи",
    price: "159 ₽",
    unit: "шт",
    rating: "4.8",
    badge: "fresh",
    badgeVariant: "success",
  },
  {
    id: "bread",
    title: "Чиабатта на закваске",
    href: "/products/ciabatta",
    imageUrl: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?auto=format&fit=crop&w=600&q=80",
    category: "Выпечка",
    price: "139 ₽",
    oldPrice: "159 ₽",
    unit: "250 г",
    rating: "4.9",
    badge: "утро",
    badgeVariant: "info",
  },
];

export const newProducts: HomeProduct[] = [
  {
    id: "berry-yogurt",
    title: "Йогурт с лесными ягодами",
    href: "/products/berry-yogurt",
    imageUrl: "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80",
    category: "Новинки",
    price: "86 ₽",
    unit: "180 г",
    rating: "4.6",
    badge: "new",
    badgeVariant: "primary",
  },
  {
    id: "granola",
    title: "Гранола миндаль и мёд",
    href: "/products/granola-honey",
    imageUrl: "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=600&q=80",
    category: "Завтраки",
    price: "249 ₽",
    unit: "350 г",
    rating: "4.7",
    badge: "new",
    badgeVariant: "primary",
  },
  {
    id: "kombucha",
    title: "Комбуча имбирь-лимон",
    href: "/products/kombucha-ginger",
    imageUrl: "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=600&q=80",
    category: "Напитки",
    price: "139 ₽",
    unit: "330 мл",
    rating: "4.5",
    badge: "new",
    badgeVariant: "primary",
  },
  {
    id: "cheese",
    title: "Сыр козий мягкий",
    href: "/products/goat-cheese",
    imageUrl: "https://images.unsplash.com/photo-1452195100486-9cc805987862?auto=format&fit=crop&w=600&q=80",
    category: "Сыры",
    price: "329 ₽",
    unit: "160 г",
    rating: "4.8",
    badge: "new",
    badgeVariant: "primary",
  },
];

export const recommendations: HomeProduct[] = [
  {
    id: "tomatoes",
    title: "Томаты черри сладкие",
    href: "/products/cherry-tomatoes",
    imageUrl: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80",
    category: "Овощи",
    price: "219 ₽",
    unit: "250 г",
    rating: "4.8",
  },
  {
    id: "eggs",
    title: "Яйца деревенские C0",
    href: "/products/farm-eggs",
    imageUrl: "https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=600&q=80",
    category: "Фермерское",
    price: "179 ₽",
    unit: "10 шт",
    rating: "4.9",
  },
  {
    id: "spinach",
    title: "Шпинат baby washed",
    href: "/products/baby-spinach",
    imageUrl: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=600&q=80",
    category: "Зелень",
    price: "149 ₽",
    unit: "125 г",
    rating: "4.7",
  },
  {
    id: "coffee",
    title: "Кофе зерновой medium roast",
    href: "/products/coffee-medium",
    imageUrl: "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=600&q=80",
    category: "Бакалея",
    price: "699 ₽",
    unit: "500 г",
    rating: "4.8",
  },
];

export const farmerProducts: HomeProduct[] = [
  {
    id: "farm-honey",
    title: "Мёд липовый фермерский",
    href: "/products/linden-honey",
    imageUrl: "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80",
    category: "Фермерское",
    price: "459 ₽",
    unit: "450 г",
    rating: "4.9",
    badge: "ферма",
    badgeVariant: "success",
  },
  {
    id: "farm-curd",
    title: "Творог зерновой",
    href: "/products/grain-curd",
    imageUrl: "https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=600&q=80",
    category: "Молочные",
    price: "169 ₽",
    unit: "300 г",
    rating: "4.8",
    badge: "ферма",
    badgeVariant: "success",
  },
  {
    id: "farm-greens",
    title: "Микс зелени сезонный",
    href: "/products/season-greens",
    imageUrl: "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80",
    category: "Зелень",
    price: "189 ₽",
    unit: "150 г",
    rating: "4.7",
    badge: "ферма",
    badgeVariant: "success",
  },
];

export const brands: HomeBrand[] = [
  {
    id: "green-line",
    title: "Зелёная линия",
    href: "/brands/green-line",
    imageUrl: "https://images.unsplash.com/photo-1498579397066-22750a3cb424?auto=format&fit=crop&w=600&q=80",
    description: "Овощи, зелень и сезонные наборы",
    badge: "eco",
  },
  {
    id: "milk-yard",
    title: "Молочный двор",
    href: "/brands/milk-yard",
    imageUrl: "https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=600&q=80",
    description: "Молоко, творог, йогурты",
    badge: "farm",
  },
  {
    id: "north-fish",
    title: "Северная рыба",
    href: "/brands/north-fish",
    imageUrl: "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=600&q=80",
    description: "Охлаждённая рыба и деликатесы",
    badge: "fresh",
  },
  {
    id: "daily-bakery",
    title: "Daily Bakery",
    href: "/brands/daily-bakery",
    imageUrl: "https://images.unsplash.com/photo-1517433670267-08bbd4be890f?auto=format&fit=crop&w=600&q=80",
    description: "Хлеб, круассаны, десерты",
    badge: "morning",
  },
];

export const deliveryBenefits: HomeBenefit[] = [
  {
    id: "time",
    title: "Интервалы от 60 минут",
    description: "Выберите удобное окно доставки или самовывоз из ближайшего пункта.",
  },
  {
    id: "cold",
    title: "Холодовая цепь",
    description: "Молочные продукты, мясо и рыба приезжают в термоупаковке.",
  },
  {
    id: "quality",
    title: "Контроль свежести",
    description: "Сборщик проверяет срок годности, внешний вид и целостность упаковки.",
  },
  {
    id: "support",
    title: "Поддержка заказов",
    description: "Операторы помогают с заменой, оплатой, возвратами и статусом доставки.",
  },
];

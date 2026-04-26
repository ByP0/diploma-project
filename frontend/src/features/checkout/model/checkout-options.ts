import type {
  CheckoutFormState,
  DeliveryMethod,
  DeliveryOption,
  DeliveryWindowOption,
  PaymentOption,
  PaymentProviderOption,
} from "./checkout.types";

export const checkoutSteps = [
  { id: "items", title: "Товары", description: "Проверка корзины" },
  { id: "address", title: "Адрес", description: "Контакты и доставка" },
  { id: "delivery", title: "Доставка", description: "Способ и интервал" },
  { id: "payment", title: "Оплата", description: "Метод платежа" },
  { id: "summary", title: "Итог", description: "Price lock" },
] as const;

export const deliveryOptions: DeliveryOption[] = [
  {
    id: "courier",
    title: "Курьерская доставка",
    description: "Оптимально для больших продуктовых заказов.",
    eta: "Сегодня или завтра",
    badge: "Популярно",
    priceHint: "Расчёт на summary",
  },
  {
    id: "express",
    title: "Экспресс",
    description: "Приоритетная сборка и ближайший слот.",
    eta: "От 60 минут",
    badge: "Быстро",
    priceHint: "Повышенный тариф",
  },
  {
    id: "pickup",
    title: "Самовывоз",
    description: "Заберите заказ из ближайшей точки выдачи.",
    eta: "После сборки",
    priceHint: "0 ₽",
  },
];

export const paymentOptions: PaymentOption[] = [
  {
    id: "card_online",
    title: "Картой онлайн",
    description: "Цена фиксируется сразу после создания заказа.",
    badge: "Рекомендуем",
  },
  {
    id: "card_on_delivery",
    title: "Картой при получении",
    description: "Оплата курьеру после проверки пакетов.",
  },
  {
    id: "cash_on_delivery",
    title: "Наличными при получении",
    description: "Доступно для курьерской доставки.",
  },
];

export const paymentProviderOptions: PaymentProviderOption[] = [
  {
    id: "stub_auto",
    title: "GreenPay",
    description: "Тестовый маршрут для быстрой онлайн-оплаты.",
    commissionLabel: "Комиссия 0%",
  },
  {
    id: "stub_redirect",
    title: "BankLine",
    description: "Тестовый резервный платёжный маршрут.",
    commissionLabel: "Комиссия 0%",
  },
];

export const initialCheckoutForm: CheckoutFormState = {
  customerName: "",
  customerPhone: "",
  customerComment: "",
  deliveryMethod: "courier",
  deliveryWindowId: "today-evening",
  deliveryAddressLine1: "",
  deliveryAddressLine2: "",
  deliveryCity: "Калининград",
  deliveryRegion: "Калининградская область",
  deliveryPostalCode: "",
  deliveryCountry: "RU",
  deliveryFloor: "",
  deliveryApartment: "",
  deliveryEntrance: "",
  deliveryIntercom: "",
  deliveryInstructions: "",
  paymentMethod: "card_online",
  paymentProvider: "stub_auto",
  currency: "RUB",
};

export function buildDeliveryWindows(): DeliveryWindowOption[] {
  const now = new Date();
  return [
    buildWindow("today-evening", "Сегодня", "18:00-21:00", now, 18, 21),
    buildWindow("tomorrow-morning", "Завтра", "09:00-12:00", addDays(now, 1), 9, 12),
    buildWindow("tomorrow-day", "Завтра", "13:00-16:00", addDays(now, 1), 13, 16),
    buildWindow("tomorrow-evening", "Завтра", "18:00-21:00", addDays(now, 1), 18, 21),
  ];
}

export function getDeliveryOption(method: DeliveryMethod) {
  return deliveryOptions.find((option) => option.id === method) ?? deliveryOptions[0];
}

function buildWindow(
  id: string,
  title: string,
  description: string,
  baseDate: Date,
  startHour: number,
  endHour: number,
): DeliveryWindowOption {
  const start = new Date(baseDate);
  start.setHours(startHour, 0, 0, 0);
  const end = new Date(baseDate);
  end.setHours(endHour, 0, 0, 0);

  return {
    id,
    title,
    description,
    start: start.toISOString(),
    end: end.toISOString(),
  };
}

function addDays(date: Date, days: number) {
  const nextDate = new Date(date);
  nextDate.setDate(nextDate.getDate() + days);
  return nextDate;
}

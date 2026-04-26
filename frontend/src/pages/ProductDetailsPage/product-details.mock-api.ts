import type {
  AddToCartPayload,
  AddToCartResult,
  ProductDetails,
  ProductDetailsResponse,
  ProductPriceQuote,
  ProductStockStatus,
} from "./product-details.types";

const LOW_STOCK_THRESHOLD = 8;

const mockProduct: ProductDetails = {
  id: "banana-organic-premium",
  sku: "BANAN-001",
  title: "Бананы органические Premium, Эквадор",
  brand: "Ферма Эко",
  brandHref: "/brands/ferma-eco",
  category: "Овощи и фрукты",
  categoryHref: "/catalog/vegetables-fruits",
  rating: 4.9,
  reviewsCount: 128,
  description:
    "Спелые органические бананы с плотной кремовой текстурой. Подходят для завтраков, смузи, выпечки и детского питания. Поставка проходит входной контроль свежести и бережную сортировку.",
  images: [
    {
      id: "banana-main",
      url: "https://images.unsplash.com/photo-1603833665858-e61d17a86224?auto=format&fit=crop&w=1000&q=85",
      alt: "Связка органических бананов",
    },
    {
      id: "banana-bunch",
      url: "https://images.unsplash.com/photo-1528825871115-3581a5387919?auto=format&fit=crop&w=1000&q=85",
      alt: "Бананы крупным планом",
    },
    {
      id: "banana-market",
      url: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=1000&q=85",
      alt: "Бананы на продуктовой полке",
    },
    {
      id: "banana-smoothie",
      url: "https://images.unsplash.com/photo-1570696516188-ade861b84a49?auto=format&fit=crop&w=1000&q=85",
      alt: "Бананы для завтрака",
    },
  ],
  characteristics: [
    { label: "Страна", value: "Эквадор" },
    { label: "Класс", value: "Premium organic" },
    { label: "Срок годности", value: "5 дней" },
    { label: "Температура хранения", value: "+12...+14 °C" },
    { label: "Пищевая ценность", value: "89 ккал / 100 г" },
    { label: "Артикул", value: "BANAN-001" },
  ],
  stock: 14,
  reservedStock: 7,
  unit: "кг",
  basePrice: 169,
  oldPrice: 199,
  currency: "RUB",
  pricingTiers: [
    { minQuantity: 1, unitPrice: 169, label: "Стандартная цена" },
    { minQuantity: 3, unitPrice: 159, label: "От 3 кг" },
    { minQuantity: 5, unitPrice: 149, label: "Семейная упаковка" },
  ],
  isFavorite: false,
  relatedProducts: [
    {
      id: "avocado-hass",
      title: "Авокадо Hass спелое",
      href: "/products/avocado-hass",
      imageUrl: "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?auto=format&fit=crop&w=600&q=80",
      price: 159,
      unit: "шт",
      rating: 4.8,
      stock: 24,
    },
    {
      id: "berry-yogurt",
      title: "Йогурт с лесными ягодами",
      href: "/products/berry-yogurt",
      imageUrl: "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80",
      price: 86,
      unit: "180 г",
      rating: 4.6,
      stock: 32,
    },
    {
      id: "granola-honey",
      title: "Гранола миндаль и мёд",
      href: "/products/granola-honey",
      imageUrl: "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=600&q=80",
      price: 249,
      unit: "350 г",
      rating: 4.7,
      stock: 18,
    },
    {
      id: "farm-milk",
      title: "Молоко фермерское 3,5%",
      href: "/products/farm-milk",
      imageUrl: "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=600&q=80",
      price: 98,
      unit: "900 мл",
      rating: 4.8,
      stock: 41,
    },
  ],
  reviews: [
    {
      id: "review-1",
      author: "Анна",
      rating: 5,
      createdAt: "2026-04-21",
      title: "Хорошая спелость",
      text: "Приехали аккуратные, без повреждений. Для смузи и завтраков отлично.",
      verifiedPurchase: true,
    },
    {
      id: "review-2",
      author: "Илья",
      rating: 5,
      createdAt: "2026-04-19",
      title: "Стабильное качество",
      text: "Беру второй раз, партия ровная. Удобно, что можно заказать сразу несколько килограммов.",
      verifiedPurchase: true,
    },
    {
      id: "review-3",
      author: "Мария",
      rating: 4,
      createdAt: "2026-04-16",
      title: "Свежие, но быстро дозревают",
      text: "Лучше брать под ближайшие пару дней. По вкусу и упаковке вопросов нет.",
      verifiedPurchase: true,
    },
  ],
  deliveryEstimates: [
    {
      method: "express",
      title: "Экспресс",
      description: "Сегодня, ближайшее окно 18:00–20:00",
      price: 249,
      eta: "2 часа",
    },
    {
      method: "courier",
      title: "Курьер",
      description: "Завтра, интервалы с 09:00",
      price: 149,
      eta: "завтра",
    },
    {
      method: "pickup",
      title: "Самовывоз",
      description: "Пункт выдачи на Советском проспекте",
      price: 0,
      eta: "сегодня",
    },
  ],
};

function wait(ms = 280) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

function getAvailableQuantity(product: ProductDetails) {
  return Math.max(product.stock - product.reservedStock, 0);
}

function getStockStatus(availableQuantity: number): ProductStockStatus {
  if (availableQuantity <= 0) {
    return "out_of_stock";
  }

  if (availableQuantity <= LOW_STOCK_THRESHOLD) {
    return "low_stock";
  }

  return "in_stock";
}

function getUrgencyLabel(availableQuantity: number) {
  if (availableQuantity <= 0) {
    return "Нет в наличии";
  }

  if (availableQuantity <= LOW_STOCK_THRESHOLD) {
    return `Осталось ${availableQuantity} ед.`;
  }

  return undefined;
}

function selectPricingTier(product: ProductDetails, quantity: number) {
  return [...product.pricingTiers]
    .sort((left, right) => right.minQuantity - left.minQuantity)
    .find((tier) => quantity >= tier.minQuantity);
}

export const productDetailsMockApi = {
  async getProduct(productId: string): Promise<ProductDetailsResponse> {
    await wait();

    if (productId !== mockProduct.id && productId !== "banana-organic") {
      throw new Error("Товар не найден");
    }

    const availableQuantity = getAvailableQuantity(mockProduct);
    const stockStatus = getStockStatus(availableQuantity);

    return {
      product: mockProduct,
      availableQuantity,
      stockStatus,
      urgencyLabel: getUrgencyLabel(availableQuantity),
    };
  },

  async getPriceQuote(productId: string, quantity: number): Promise<ProductPriceQuote> {
    await wait(120);

    const response = await this.getProduct(productId);
    const tier = selectPricingTier(response.product, quantity);
    const unitPrice = tier?.unitPrice ?? response.product.basePrice;
    const oldUnitPrice = response.product.oldPrice;
    const subtotal = unitPrice * quantity;
    const discountAmount = Math.max(((oldUnitPrice ?? response.product.basePrice) - unitPrice) * quantity, 0);

    return {
      productId,
      quantity,
      unitPrice,
      oldUnitPrice,
      subtotal,
      discountAmount,
      currency: response.product.currency,
      appliedTier: tier,
    };
  },

  async addToCart(payload: AddToCartPayload): Promise<AddToCartResult> {
    await wait(180);
    const response = await this.getProduct(payload.productId);

    if (response.availableQuantity <= 0) {
      throw new Error("Товар закончился");
    }

    if (payload.quantity > response.availableQuantity) {
      throw new Error("Запрошенное количество превышает остаток");
    }

    return {
      productId: payload.productId,
      quantity: payload.quantity,
      cartItems: payload.quantity,
    };
  },

  async toggleFavorite(productId: string, favorite: boolean): Promise<{ productId: string; favorite: boolean }> {
    await wait(140);
    return { productId, favorite };
  },
};

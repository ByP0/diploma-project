export const cartCurrencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  maximumFractionDigits: 0,
  style: "currency",
});

export function formatCartPrice(value: number) {
  return cartCurrencyFormatter.format(value);
}

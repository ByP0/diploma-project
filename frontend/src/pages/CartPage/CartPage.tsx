import { useNavigate } from "react-router-dom";
import { useCart } from "@features/cart/model/useCart";
import { AppRoutes } from "@shared/config/routes";
import type { CartItemRead, DecimalString } from "@shared/api";
import { Button, EmptyState, ErrorState, LoadingState } from "@shared/ui";
import { Icon } from "@shared/ui/Icon";
import "./CartPage.css";

function formatPrice(value: DecimalString) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return String(value);
  }

  return new Intl.NumberFormat("ru-RU", {
    currency: "RUB",
    maximumFractionDigits: 0,
    style: "currency",
  }).format(numberValue);
}

export function CartPage() {
  const navigate = useNavigate();
  const { cart, clearCart, error, isLoading, isMerging, isMutating, reloadCart, removeItem, totalAmount, totalItems, updateItem } =
    useCart();

  return (
    <div className="cart-page">
      <section className="cart-heading">
        <div>
          <span>Корзина</span>
          <h1>Ваш заказ</h1>
          <p>Проверьте количество товаров перед оформлением. Кнопки снизу всегда ведут к покупкам или оплате.</p>
        </div>
        <Button disabled={!cart.items.length || isMutating} onClick={() => void clearCart()} variant="ghost">
          Очистить корзину
        </Button>
      </section>

      <section className="cart-summary" aria-label="Сводка корзины">
        <article>
          <span>Товаров</span>
          <strong>{totalItems}</strong>
        </article>
        <article>
          <span>Сумма</span>
          <strong>{formatPrice(totalAmount)}</strong>
        </article>
        <article>
          <span>Статус</span>
          <strong>{isMerging ? "Объединяем" : "Готово"}</strong>
        </article>
      </section>

      {isLoading || isMerging ? (
        <LoadingState
          description={isMerging ? "Переносим гостевую корзину в аккаунт." : "Загружаем список товаров."}
          title={isMerging ? "Объединяем корзину" : "Загружаем корзину"}
        />
      ) : error ? (
        <ErrorState
          action={
            <Button onClick={() => void reloadCart()} variant="secondary">
              Повторить
            </Button>
          }
          description={error}
          title="Корзина недоступна"
        />
      ) : cart.items.length ? (
        <>
          <section className="cart-list" aria-label="Товары в корзине">
            {cart.items.map((item) => (
              <CartItemCard
                isMutating={isMutating}
                item={item}
                key={item.id}
                onRemove={() => void removeItem(item.product_id)}
                onUpdate={(quantity) => void updateItem(item.product_id, quantity)}
              />
            ))}
          </section>

          <section className="cart-checkout-bar" aria-label="Итог корзины">
            <Button className="cart-checkout-bar__button" onClick={() => navigate(AppRoutes.home)} variant="secondary">
              Продолжить покупки
            </Button>
            <div className="cart-checkout-bar__total">
              <span>Итого</span>
              <strong>{formatPrice(totalAmount)}</strong>
            </div>
            <Button className="cart-checkout-bar__button cart-checkout-bar__button--pay" onClick={() => navigate(AppRoutes.checkout)}>
              Перейти к оплате
            </Button>
          </section>
        </>
      ) : (
        <EmptyState
          action={
            <Button onClick={() => navigate(AppRoutes.home)} variant="secondary">
              Продолжить покупки
            </Button>
          }
          description="Добавьте продукты с главной страницы, и они появятся в списке заказа."
          title="Корзина пустая"
        />
      )}
    </div>
  );
}

type CartItemCardProps = {
  isMutating: boolean;
  item: CartItemRead;
  onRemove: () => void;
  onUpdate: (quantity: number) => void;
};

function CartItemCard({ isMutating, item, onRemove, onUpdate }: CartItemCardProps) {
  return (
    <article className="cart-item">
      <div className="cart-item__media">
        {item.product.primary_photo_url ? (
          <img alt={item.product.name} loading="lazy" src={item.product.primary_photo_url} />
        ) : (
          <Icon name="package" size={34} />
        )}
      </div>

      <div className="cart-item__content">
        <span>{item.product.sku}</span>
        <h2>{item.product.name}</h2>
        {item.product.brand ? <p>{item.product.brand}</p> : null}
      </div>

      <div className="cart-item__quantity" aria-label="Количество">
        <button
          aria-label="Уменьшить количество"
          disabled={isMutating || item.quantity <= 1}
          onClick={() => onUpdate(item.quantity - 1)}
          type="button"
        >
          <Icon name="minus" size={17} />
        </button>
        <strong>{item.quantity}</strong>
        <button
          aria-label="Увеличить количество"
          disabled={isMutating || item.quantity >= item.product.available_stock}
          onClick={() => onUpdate(item.quantity + 1)}
          type="button"
        >
          <Icon name="plus" size={17} />
        </button>
      </div>

      <div className="cart-item__price">
        <strong>{formatPrice(item.subtotal)}</strong>
        <span>
          {formatPrice(item.product.price)} / {item.product.unit}
        </span>
      </div>

      <button className="cart-item__remove" aria-label="Удалить товар" disabled={isMutating} onClick={onRemove} type="button">
        <Icon name="trash" size={18} />
      </button>
    </article>
  );
}

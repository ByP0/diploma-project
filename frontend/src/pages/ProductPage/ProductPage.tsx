import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { catalogApi } from "@features/catalog/api/catalogApi";
import { useCart } from "@features/cart/model/useCart";
import { isApiError, type CategoryRead, type DecimalString, type ProductRead } from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { Button, ErrorState, LoadingState, useToast } from "@shared/ui";
import { Icon } from "@shared/ui/Icon";
import "./ProductPage.css";

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось загрузить товар.";
}

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

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getInitials(value: string) {
  return value
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.slice(0, 1).toUpperCase())
    .join("");
}

export function ProductPage() {
  const { productId } = useParams();
  const { addItem, isMutating } = useCart();
  const { showToast } = useToast();
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [categories, setCategories] = useState<CategoryRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [product, setProduct] = useState<ProductRead | null>(null);
  const [quantity, setQuantity] = useState(1);
  const pointerStartXRef = useRef<number | null>(null);
  const ignoreNextClickRef = useRef(false);

  useEffect(() => {
    if (!productId) {
      setError("Товар не найден.");
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();

    setIsLoading(true);
    setError(null);

    Promise.all([
      catalogApi.getProduct(productId, { signal: controller.signal }),
      catalogApi.getCategories({ signal: controller.signal }),
    ])
      .then(([nextProduct, nextCategories]) => {
        if (controller.signal.aborted) {
          return;
        }

        setProduct(nextProduct);
        setCategories(nextCategories);
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [productId]);

  useEffect(() => {
    setActiveImageIndex(0);
    setQuantity(1);
  }, [product?.id]);

  const categoryById = useMemo(() => new Map(categories.map((category) => [category.id, category])), [categories]);
  const category = product ? categoryById.get(product.category_id) : undefined;

  const imageUrls = useMemo(() => {
    if (!product) {
      return [];
    }

    const urls = [product.primary_photo_url, ...product.photo_urls].filter((url): url is string => Boolean(url));
    return Array.from(new Set(urls));
  }, [product]);

  const activeImageUrl = imageUrls[activeImageIndex] ?? imageUrls[0] ?? null;
  const maxQuantity = product ? Math.max(1, product.stock) : 1;

  const showPreviousImage = () => {
    if (imageUrls.length < 2) {
      return;
    }

    setActiveImageIndex((current) => (current === 0 ? imageUrls.length - 1 : current - 1));
  };

  const showNextImage = () => {
    if (imageUrls.length < 2) {
      return;
    }

    setActiveImageIndex((current) => (current + 1) % imageUrls.length);
  };

  const handleStagePointerDown = (event: PointerEvent<HTMLButtonElement>) => {
    pointerStartXRef.current = event.clientX;
    ignoreNextClickRef.current = false;
  };

  const handleStagePointerUp = (event: PointerEvent<HTMLButtonElement>) => {
    const startX = pointerStartXRef.current;
    pointerStartXRef.current = null;

    if (startX === null || imageUrls.length < 2) {
      return;
    }

    const deltaX = event.clientX - startX;

    if (Math.abs(deltaX) < 40) {
      return;
    }

    ignoreNextClickRef.current = true;

    if (deltaX < 0) {
      showNextImage();
    } else {
      showPreviousImage();
    }
  };

  const handleStageClick = () => {
    if (ignoreNextClickRef.current) {
      ignoreNextClickRef.current = false;
      return;
    }

    showNextImage();
  };

  const handleQuantityInput = (value: string) => {
    const nextQuantity = Number(value);

    if (!Number.isFinite(nextQuantity)) {
      return;
    }

    setQuantity(Math.min(Math.max(1, Math.floor(nextQuantity)), maxQuantity));
  };

  const handleAddToCart = async () => {
    if (!product || product.stock < 1) {
      return;
    }

    const safeQuantity = Math.min(quantity, product.stock);

    try {
      await addItem(product.id, safeQuantity);
      showToast({
        description: `${product.name}, ${safeQuantity} ${product.unit}`,
        title: "Товар добавлен в корзину",
        variant: "success",
      });
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Не удалось добавить товар",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <LoadingState description="Собираем фотографии и характеристики товара." title="Загружаем товар" />;
  }

  if (error || !product) {
    return (
      <ErrorState
        action={
          <Link className="product-detail__state-link" to={AppRoutes.home}>
            Вернуться в каталог
          </Link>
        }
        description={error ?? "Запрошенный товар не найден."}
        title="Товар недоступен"
      />
    );
  }

  const hasMultipleImages = imageUrls.length > 1;
  const stockLabel = product.stock > 0 ? `В наличии: ${product.stock} ${product.unit}` : "Нет в наличии";

  return (
    <div className="product-detail">
      <Link className="product-detail__back" to={AppRoutes.home}>
        <Icon name="arrow-left" size={18} />
        <span>К витрине</span>
      </Link>

      <section className="product-detail__main" aria-label={product.name}>
        <div className="product-gallery">
          <button
            aria-label={hasMultipleImages ? "Показать следующее фото" : "Фото товара"}
            className="product-gallery__stage"
            disabled={!hasMultipleImages}
            onClick={handleStageClick}
            onPointerDown={handleStagePointerDown}
            onPointerUp={handleStagePointerUp}
            type="button"
          >
            {activeImageUrl ? <img alt={product.name} src={activeImageUrl} /> : <span>{getInitials(product.name)}</span>}
          </button>

          {hasMultipleImages ? (
            <div className="product-gallery__controls" aria-label="Переключение фотографий">
              <button aria-label="Предыдущее фото" onClick={showPreviousImage} type="button">
                <Icon name="arrow-left" size={18} />
              </button>
              <span>
                {activeImageIndex + 1} / {imageUrls.length}
              </span>
              <button aria-label="Следующее фото" onClick={showNextImage} type="button">
                <Icon name="arrow-right" size={18} />
              </button>
            </div>
          ) : null}

          {imageUrls.length ? (
            <div className="product-gallery__thumbs" aria-label="Фотографии товара">
              {imageUrls.map((imageUrl, index) => (
                <button
                  aria-label={`Показать фото ${index + 1}`}
                  className={index === activeImageIndex ? "is-active" : undefined}
                  key={imageUrl}
                  onClick={() => setActiveImageIndex(index)}
                  type="button"
                >
                  <img alt="" src={imageUrl} />
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <aside className="product-detail__purchase" aria-label="Покупка товара">
          <p className="product-detail__category">{category?.name || "Продукты"}</p>
          <h1>{product.name}</h1>
          {product.brand ? <p className="product-detail__brand">{product.brand}</p> : null}

          <div className="product-detail__price-row">
            <strong>{formatPrice(product.price)}</strong>
            <span>{stockLabel}</span>
          </div>

          <div className="product-detail__quantity" aria-label="Количество">
            <button
              aria-label="Уменьшить количество"
              disabled={quantity <= 1 || product.stock < 1}
              onClick={() => setQuantity((current) => Math.max(1, current - 1))}
              type="button"
            >
              <Icon name="minus" size={18} />
            </button>
            <input
              aria-label="Количество товара"
              disabled={product.stock < 1}
              max={maxQuantity}
              min={1}
              onChange={(event) => handleQuantityInput(event.target.value)}
              type="number"
              value={quantity}
            />
            <button
              aria-label="Увеличить количество"
              disabled={quantity >= product.stock || product.stock < 1}
              onClick={() => setQuantity((current) => Math.min(maxQuantity, current + 1))}
              type="button"
            >
              <Icon name="plus" size={18} />
            </button>
          </div>

          <Button
            className="product-detail__cart-button"
            disabled={product.stock < 1}
            isLoading={isMutating}
            leftSlot={<Icon name="cart" size={19} />}
            onClick={() => void handleAddToCart()}
          >
            Добавить в корзину
          </Button>
        </aside>
      </section>

      <section className="product-detail__content" aria-label="Информация о товаре">
        <article className="product-detail__description">
          <span>Описание</span>
          <p>{product.description}</p>
        </article>

        <dl className="product-detail__specs">
          <div>
            <dt>Артикул</dt>
            <dd>{product.sku}</dd>
          </div>
          <div>
            <dt>Категория</dt>
            <dd>{category?.name || `ID ${product.category_id}`}</dd>
          </div>
          <div>
            <dt>Бренд</dt>
            <dd>{product.brand || "Не указан"}</dd>
          </div>
          <div>
            <dt>Единица</dt>
            <dd>{product.unit}</dd>
          </div>
          <div>
            <dt>Остаток</dt>
            <dd>{product.stock}</dd>
          </div>
          <div>
            <dt>Статус</dt>
            <dd>{product.is_active ? "Активен" : "Снят с витрины"}</dd>
          </div>
          <div>
            <dt>Фото</dt>
            <dd>{imageUrls.length}</dd>
          </div>
          <div>
            <dt>ID товара</dt>
            <dd>{product.id}</dd>
          </div>
          <div>
            <dt>Создан</dt>
            <dd>{formatDate(product.created_at)}</dd>
          </div>
          <div>
            <dt>Обновлен</dt>
            <dd>{formatDate(product.updated_at)}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}

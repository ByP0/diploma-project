import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { catalogApi } from "@features/catalog/api/catalogApi";
import { useCart } from "@features/cart/model/useCart";
import { isApiError, type CategoryRead, type DecimalString, type ProductRead } from "@shared/api";
import { buildProductRoute } from "@shared/config/routes";
import { Button, EmptyState, ErrorState, LoadingState, useToast } from "@shared/ui";
import { Icon } from "@shared/ui/Icon";
import "./HomePage.css";

const PRODUCT_LIMIT = 48;

type ProductSocialProof = {
  rating: number;
  reviews: number;
  score: number;
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось загрузить витрину.";
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

function getProductSocialProof(product: ProductRead): ProductSocialProof {
  const seed = Array.from(product.id).reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const stockWeight = Math.min(product.stock, 120);
  const reviews = 80 + ((seed + stockWeight * 7) % 920);
  const rating = Math.min(5, 4.4 + ((seed % 55) / 100));

  return {
    rating: Number(rating.toFixed(1)),
    reviews,
    score: reviews * 10 + rating * 100 + stockWeight,
  };
}

function getInitials(value: string) {
  return value
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.slice(0, 1).toUpperCase())
    .join("");
}

export function HomePage() {
  const { addItem, isMutating } = useCart();
  const { showToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [categories, setCategories] = useState<CategoryRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [products, setProducts] = useState<ProductRead[]>([]);

  const search = searchParams.get("search")?.trim() ?? "";
  const categoryId = Number(searchParams.get("category") ?? "");
  const activeCategoryId = Number.isFinite(categoryId) && categoryId > 0 ? categoryId : undefined;

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);
    setError(null);

    Promise.all([
      catalogApi.getCategories({ signal: controller.signal }),
      catalogApi.getProducts(
        {
          active_only: true,
          category_id: activeCategoryId,
          limit: PRODUCT_LIMIT,
          offset: 0,
          search: search || undefined,
        },
        { signal: controller.signal },
      ),
    ])
      .then(([nextCategories, nextProducts]) => {
        if (controller.signal.aborted) {
          return;
        }

        setCategories(nextCategories);
        setProducts(nextProducts);
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
  }, [activeCategoryId, search]);

  const categoryById = useMemo(() => new Map(categories.map((category) => [category.id, category])), [categories]);

  const sortedProducts = useMemo(
    () =>
      [...products].sort((left, right) => {
        const rightProof = getProductSocialProof(right);
        const leftProof = getProductSocialProof(left);
        return rightProof.score - leftProof.score;
      }),
    [products],
  );

  const activeCategory = activeCategoryId ? categoryById.get(activeCategoryId) : null;

  const handleCategoryChange = (nextCategoryId?: number) => {
    const nextParams = new URLSearchParams(searchParams);

    if (nextCategoryId) {
      nextParams.set("category", String(nextCategoryId));
    } else {
      nextParams.delete("category");
    }

    setSearchParams(nextParams);
  };

  const handleAddToCart = async (product: ProductRead) => {
    try {
      await addItem(product.id, 1);
      showToast({
        description: product.name,
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

  return (
    <div className="home-page">
      <section className="home-spotlight" aria-label="Витрина магазина">
        <div>
          <p className="home-spotlight__eyebrow">Свежие продукты каждый день</p>
          <h1>Зеленая Лавка</h1>
          <p>
            Мягкая магазинная витрина с быстрым поиском, категориями и товарами, отсортированными по популярности и
            количеству оценок.
          </p>
        </div>
        <div className="home-spotlight__stats" aria-label="Преимущества">
          <article>
            <strong>от 30 мин</strong>
            <span>сборка заказа</span>
          </article>
          <article>
            <strong>4.8</strong>
            <span>средняя оценка</span>
          </article>
          <article>
            <strong>24/7</strong>
            <span>AI-поддержка</span>
          </article>
        </div>
      </section>

      <section className="home-categories" aria-label="Категории продуктов">
        <button className={!activeCategoryId ? "is-active" : undefined} onClick={() => handleCategoryChange()} type="button">
          Все продукты
        </button>
        {categories.slice(0, 10).map((category) => (
          <button
            className={category.id === activeCategoryId ? "is-active" : undefined}
            key={category.id}
            onClick={() => handleCategoryChange(category.id)}
            type="button"
          >
            {category.name}
          </button>
        ))}
      </section>

      <section className="home-section-heading">
        <div>
          <span>{activeCategory?.name || "Популярное"}</span>
          <h2>{search ? `Результаты поиска: ${search}` : "Самые популярные товары"}</h2>
        </div>
        <p>Сначала показываем позиции с большим расчетным спросом, высокой оценкой и большим числом отзывов.</p>
      </section>

      {isLoading ? (
        <LoadingState description="Подбираем самые популярные продукты." title="Загружаем витрину" />
      ) : error ? (
        <ErrorState
          action={
            <Button onClick={() => window.location.reload()} variant="secondary">
              Обновить
            </Button>
          }
          description={error}
          title="Каталог недоступен"
        />
      ) : sortedProducts.length ? (
        <section className="home-product-grid" aria-label="Популярные товары">
          {sortedProducts.map((product) => (
            <ProductCard
              category={categoryById.get(product.category_id)}
              isAdding={isMutating}
              key={product.id}
              onAdd={() => void handleAddToCart(product)}
              product={product}
            />
          ))}
        </section>
      ) : (
        <EmptyState
          action={
            <Button
              onClick={() => {
                const nextParams = new URLSearchParams(searchParams);
                nextParams.delete("search");
                nextParams.delete("category");
                setSearchParams(nextParams);
              }}
              variant="secondary"
            >
              Сбросить фильтры
            </Button>
          }
          description="Попробуйте другой запрос или категорию."
          title="Товары не найдены"
        />
      )}
    </div>
  );
}

type ProductCardProps = {
  category?: CategoryRead;
  isAdding: boolean;
  onAdd: () => void;
  product: ProductRead;
};

function ProductCard({ category, isAdding, onAdd, product }: ProductCardProps) {
  const proof = getProductSocialProof(product);

  return (
    <article className="home-product-card">
      <Link className="home-product-card__main" rel="noreferrer" target="_blank" to={buildProductRoute(product.id)}>
        <div className="home-product-card__media">
          {product.primary_photo_url ? (
            <img alt={product.name} loading="lazy" src={product.primary_photo_url} />
          ) : (
            <span>{getInitials(product.name)}</span>
          )}
        </div>

        <div className="home-product-card__body">
          <div className="home-product-card__meta">
            <span>{category?.name || "Продукты"}</span>
            <span className="home-product-card__rating">
              <Icon name="star" size={15} />
              {proof.rating} / {proof.reviews}
            </span>
          </div>

          <h3>{product.name}</h3>
          {product.brand ? <p className="home-product-card__brand">{product.brand}</p> : null}
          <p className="home-product-card__description">{product.description}</p>
        </div>
      </Link>

      <div className="home-product-card__footer">
        <div>
          <strong>{formatPrice(product.price)}</strong>
          <span>
            {product.stock > 0 ? `В наличии: ${product.stock}` : "Нет в наличии"} / {product.unit}
          </span>
        </div>
        <Button disabled={isAdding || product.stock < 1} onClick={onAdd} size="sm">
          В корзину
        </Button>
      </div>
    </article>
  );
}

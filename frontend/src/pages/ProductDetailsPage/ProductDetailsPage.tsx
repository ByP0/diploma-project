import * as React from "react";

import { CartIcon, HeartIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { cn } from "../../shared/lib/cn";
import { Badge } from "../../shared/ui/Badge";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Skeleton, SkeletonText } from "../../shared/ui/Skeleton";
import { productDetailsMockApi } from "./product-details.mock-api";
import type {
  DeliveryEstimate,
  ProductDetails,
  ProductImage,
  ProductPriceQuote,
  ProductReview,
  ProductStockStatus,
  RelatedProduct,
} from "./product-details.types";
import { useProductDetails } from "./use-product-details";

export interface ProductDetailsPageProps {
  productId?: string;
  LinkComponent?: StorefrontLinkComponent;
  onCartAdded?: (productId: string, quantity: number) => void;
  onFavoriteChange?: (productId: string, favorite: boolean) => void;
  className?: string;
}

const defaultProductId = "banana-organic-premium";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  currency: "RUB",
  maximumFractionDigits: 0,
  style: "currency",
});

export function ProductDetailsPage({
  productId = defaultProductId,
  LinkComponent,
  onCartAdded,
  onFavoriteChange,
  className,
}: ProductDetailsPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const [quantity, setQuantity] = React.useState(1);
  const [favorite, setFavorite] = React.useState(false);
  const [selectedImageId, setSelectedImageId] = React.useState<string | null>(null);
  const [isAddingToCart, setIsAddingToCart] = React.useState(false);
  const [isFavoriteLoading, setIsFavoriteLoading] = React.useState(false);
  const [actionMessage, setActionMessage] = React.useState<string | null>(null);

  const { data, quote, loading, quoteLoading, error, reload } = useProductDetails(productId, quantity);

  React.useEffect(() => {
    if (!data) {
      return;
    }

    setFavorite(data.product.isFavorite);
    setSelectedImageId((currentImageId) => {
      const imageStillExists = data.product.images.some((image) => image.id === currentImageId);
      return imageStillExists ? currentImageId : data.product.images[0]?.id ?? null;
    });
    setQuantity((currentQuantity) => Math.min(Math.max(currentQuantity, 1), Math.max(data.availableQuantity, 1)));
  }, [data]);

  if (loading) {
    return <ProductDetailsSkeleton className={className} />;
  }

  if (error || !data) {
    return (
      <Card className={cn("p-6", className)} variant="surface">
        <h1 className="text-h2 text-foreground">Не удалось загрузить товар</h1>
        <p className="mt-2 text-body-sm text-muted-foreground">{error ?? "Попробуйте обновить страницу."}</p>
        <Button className="mt-5" onClick={reload}>
          Повторить
        </Button>
      </Card>
    );
  }

  const { product, availableQuantity, stockStatus, urgencyLabel } = data;
  const selectedImage = product.images.find((image) => image.id === selectedImageId) ?? product.images[0];
  const isOutOfStock = stockStatus === "out_of_stock";
  const maxQuantity = Math.max(availableQuantity, 1);

  const handleQuantityChange = (nextQuantity: number) => {
    setActionMessage(null);
    setQuantity(Math.min(Math.max(nextQuantity, 1), maxQuantity));
  };

  const handleAddToCart = async () => {
    if (isOutOfStock) {
      return;
    }

    setActionMessage(null);
    setIsAddingToCart(true);

    try {
      await productDetailsMockApi.addToCart({ productId: product.id, quantity });
      setActionMessage(`Добавлено в корзину: ${quantity} ${product.unit}`);
      onCartAdded?.(product.id, quantity);
    } catch (requestError) {
      setActionMessage(requestError instanceof Error ? requestError.message : "Не удалось добавить товар");
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleFavoriteToggle = async () => {
    const nextFavorite = !favorite;
    setIsFavoriteLoading(true);
    setActionMessage(null);

    try {
      const result = await productDetailsMockApi.toggleFavorite(product.id, nextFavorite);
      setFavorite(result.favorite);
      onFavoriteChange?.(product.id, result.favorite);
    } catch {
      setActionMessage("Не удалось обновить избранное");
    } finally {
      setIsFavoriteLoading(false);
    }
  };

  return (
    <div className={cn("grid gap-6", className)}>
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <ProductGallery
          images={product.images}
          selectedImage={selectedImage}
          onImageSelect={(imageId) => setSelectedImageId(imageId)}
        />

        <ProductPurchasePanel
          actionMessage={actionMessage}
          availableQuantity={availableQuantity}
          favorite={favorite}
          isAddingToCart={isAddingToCart}
          isFavoriteLoading={isFavoriteLoading}
          isOutOfStock={isOutOfStock}
          Link={Link}
          onAddToCart={handleAddToCart}
          onFavoriteToggle={handleFavoriteToggle}
          onQuantityChange={handleQuantityChange}
          product={product}
          quantity={quantity}
          quote={quote}
          quoteLoading={quoteLoading}
          stockStatus={stockStatus}
          urgencyLabel={urgencyLabel}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="grid gap-6">
          <DescriptionCard product={product} />
          <ReviewsSection reviews={product.reviews} rating={product.rating} reviewsCount={product.reviewsCount} />
        </div>
        <DeliveryEstimateSection estimates={product.deliveryEstimates} />
      </section>

      <RelatedProductsSection Link={Link} products={product.relatedProducts} />
    </div>
  );
}

function ProductGallery({
  images,
  selectedImage,
  onImageSelect,
}: {
  images: ProductImage[];
  selectedImage?: ProductImage;
  onImageSelect: (imageId: string) => void;
}) {
  return (
    <Card className="grid gap-4 p-4 lg:grid-cols-[88px_minmax(0,1fr)]" variant="surface">
      <div className="order-2 flex gap-2 overflow-x-auto scrollbar-soft lg:order-1 lg:grid lg:max-h-[580px] lg:overflow-y-auto">
        {images.map((image) => (
          <button
            aria-label={`Показать изображение: ${image.alt}`}
            className={cn(
              "focus-ring h-20 w-20 shrink-0 overflow-hidden rounded-md border bg-muted transition",
              selectedImage?.id === image.id ? "border-primary shadow-focus" : "border-border hover:border-primary-border",
            )}
            key={image.id}
            onClick={() => onImageSelect(image.id)}
            type="button"
          >
            <img alt="" className="h-full w-full object-cover" loading="lazy" src={image.url} />
          </button>
        ))}
      </div>

      <div className="order-1 overflow-hidden rounded-lg bg-muted lg:order-2">
        {selectedImage ? (
          <img
            alt={selectedImage.alt}
            className="aspect-square h-full w-full object-cover"
            src={selectedImage.url}
          />
        ) : (
          <div className="aspect-square" />
        )}
      </div>
    </Card>
  );
}

function ProductPurchasePanel({
  product,
  Link,
  quote,
  quoteLoading,
  quantity,
  availableQuantity,
  stockStatus,
  urgencyLabel,
  favorite,
  isOutOfStock,
  isAddingToCart,
  isFavoriteLoading,
  actionMessage,
  onQuantityChange,
  onAddToCart,
  onFavoriteToggle,
}: {
  product: ProductDetails;
  Link: StorefrontLinkComponent;
  quote: ProductPriceQuote | null;
  quoteLoading: boolean;
  quantity: number;
  availableQuantity: number;
  stockStatus: ProductStockStatus;
  urgencyLabel?: string;
  favorite: boolean;
  isOutOfStock: boolean;
  isAddingToCart: boolean;
  isFavoriteLoading: boolean;
  actionMessage: string | null;
  onQuantityChange: (quantity: number) => void;
  onAddToCart: () => void;
  onFavoriteToggle: () => void;
}) {
  return (
    <Card className="p-5" variant="surface">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="primary">{product.category}</Badge>
        <Badge variant={stockStatus === "out_of_stock" ? "danger" : stockStatus === "low_stock" ? "warning" : "success"}>
          {stockStatus === "out_of_stock" ? "Нет в наличии" : stockStatus === "low_stock" ? "Мало" : "В наличии"}
        </Badge>
        {urgencyLabel && stockStatus !== "out_of_stock" ? <Badge variant="warning">{urgencyLabel}</Badge> : null}
      </div>

      <h1 className="mt-4 text-h1 text-foreground">{product.title}</h1>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-body-sm">
        <Link className="font-bold text-primary-active hover:text-primary-hover" href={product.brandHref}>
          {product.brand}
        </Link>
        <span className="text-muted-foreground">Артикул: {product.sku}</span>
        <span className="font-bold text-warning">★ {product.rating}</span>
        <a className="font-semibold text-primary-active hover:text-primary-hover" href="#reviews">
          {product.reviewsCount} отзывов
        </a>
      </div>

      <p className="mt-4 text-body text-muted-foreground">{product.description}</p>

      <div className="mt-5 rounded-lg border border-border bg-surface-raised p-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-caption font-bold uppercase text-muted-foreground">Цена</p>
            <div className="mt-1 flex items-baseline gap-2">
              <p className="text-display-md font-black text-foreground">
                {formatPrice(quote?.unitPrice ?? product.basePrice)}
                <span className="ml-1 text-body-sm font-semibold text-muted-foreground">/{product.unit}</span>
              </p>
              {quote?.oldUnitPrice ? (
                <p className="text-body-sm font-semibold text-muted-foreground line-through">
                  {formatPrice(quote.oldUnitPrice)}
                </p>
              ) : null}
            </div>
            {quote?.appliedTier ? (
              <p className="mt-1 text-caption font-semibold text-success">{quote.appliedTier.label}</p>
            ) : null}
          </div>

          <div className="min-w-[180px] rounded-md border border-border bg-surface px-3 py-2">
            <p className="text-caption text-muted-foreground">Итого</p>
            <p className="text-h3 text-foreground">
              {quoteLoading ? "..." : formatPrice(quote?.subtotal ?? product.basePrice * quantity)}
            </p>
            {quote?.discountAmount ? (
              <p className="text-caption font-semibold text-success">Выгода {formatPrice(quote.discountAmount)}</p>
            ) : null}
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-center">
          <QuantityStepper
            disabled={isOutOfStock}
            max={Math.max(availableQuantity, 1)}
            onChange={onQuantityChange}
            value={quantity}
          />
          <p className="text-body-sm text-muted-foreground">
            Доступно к заказу: <span className="font-bold text-foreground">{availableQuantity}</span> {product.unit}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
        <Button
          disabled={isOutOfStock}
          fullWidth
          leftIcon={<CartIcon />}
          loading={isAddingToCart}
          onClick={onAddToCart}
          size="lg"
        >
          {isOutOfStock ? "Нет в наличии" : "Добавить в корзину"}
        </Button>
        <Button
          aria-pressed={favorite}
          disabled={isFavoriteLoading}
          leftIcon={<HeartIcon />}
          onClick={onFavoriteToggle}
          size="lg"
          variant={favorite ? "soft" : "secondary"}
        >
          {favorite ? "В избранном" : "В избранное"}
        </Button>
      </div>

      {actionMessage ? (
        <p className="mt-3 rounded-md border border-primary-border bg-primary-soft px-3 py-2 text-body-sm font-semibold text-primary-active" role="status">
          {actionMessage}
        </p>
      ) : null}
    </Card>
  );
}

function QuantityStepper({
  value,
  max,
  disabled,
  onChange,
}: {
  value: number;
  max: number;
  disabled?: boolean;
  onChange: (value: number) => void;
}) {
  return (
    <div className="inline-grid w-[156px] grid-cols-[44px_minmax(0,1fr)_44px] overflow-hidden rounded-md border border-border bg-surface">
      <button
        aria-label="Уменьшить количество"
        className="focus-ring min-h-[44px] border-r border-border font-black text-foreground disabled:cursor-not-allowed disabled:opacity-40"
        disabled={disabled || value <= 1}
        onClick={() => onChange(value - 1)}
        type="button"
      >
        -
      </button>
      <input
        aria-label="Количество"
        className="min-w-0 border-0 bg-transparent text-center text-body-sm font-bold text-foreground focus:outline-none"
        disabled={disabled}
        max={max}
        min={1}
        onChange={(event) => onChange(Number(event.target.value) || 1)}
        type="number"
        value={value}
      />
      <button
        aria-label="Увеличить количество"
        className="focus-ring min-h-[44px] border-l border-border font-black text-foreground disabled:cursor-not-allowed disabled:opacity-40"
        disabled={disabled || value >= max}
        onClick={() => onChange(value + 1)}
        type="button"
      >
        +
      </button>
    </div>
  );
}

function DescriptionCard({ product }: { product: ProductDetails }) {
  return (
    <Card className="p-5" variant="surface">
      <h2 className="text-h2 text-foreground">Описание и характеристики</h2>
      <p className="mt-3 text-body text-muted-foreground">{product.description}</p>

      <dl className="mt-5 grid gap-0 overflow-hidden rounded-lg border border-border sm:grid-cols-2">
        {product.characteristics.map((item) => (
          <div className="grid grid-cols-[minmax(120px,0.8fr)_minmax(0,1fr)] border-b border-border bg-surface last:border-b-0 sm:odd:border-r" key={item.label}>
            <dt className="bg-surface-raised px-4 py-3 text-body-sm font-semibold text-muted-foreground">{item.label}</dt>
            <dd className="px-4 py-3 text-body-sm font-bold text-foreground">{item.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

function DeliveryEstimateSection({ estimates }: { estimates: DeliveryEstimate[] }) {
  return (
    <Card className="p-5" variant="surface">
      <h2 className="text-h3 text-foreground">Доставка</h2>
      <p className="mt-1 text-body-sm text-muted-foreground">Расчёт для текущего склада и ближайших интервалов.</p>
      <div className="mt-4 grid gap-3">
        {estimates.map((estimate) => (
          <div className="rounded-lg border border-border bg-surface-raised p-4" key={estimate.method}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-body-sm font-black text-foreground">{estimate.title}</p>
                <p className="mt-1 text-body-sm text-muted-foreground">{estimate.description}</p>
              </div>
              <Badge variant={estimate.price === 0 ? "success" : "primary"}>
                {estimate.price === 0 ? "Бесплатно" : formatPrice(estimate.price)}
              </Badge>
            </div>
            <p className="mt-3 text-caption font-semibold text-primary-active">Оценка: {estimate.eta}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ReviewsSection({
  reviews,
  rating,
  reviewsCount,
}: {
  reviews: ProductReview[];
  rating: number;
  reviewsCount: number;
}) {
  return (
    <Card className="p-5" id="reviews" variant="surface">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-h2 text-foreground">Отзывы</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">
            Средняя оценка {rating} на основе {reviewsCount} отзывов.
          </p>
        </div>
        <Button variant="secondary">Оставить отзыв</Button>
      </div>

      <div className="mt-5 grid gap-3">
        {reviews.map((review) => (
          <article className="rounded-lg border border-border bg-surface-raised p-4" key={review.id}>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-body-sm font-black text-foreground">{review.author}</p>
              <span className="text-caption font-bold text-warning">★ {review.rating}</span>
              {review.verifiedPurchase ? <Badge variant="success">Проверенная покупка</Badge> : null}
              <time className="text-caption text-muted-foreground" dateTime={review.createdAt}>
                {formatDate(review.createdAt)}
              </time>
            </div>
            <h3 className="mt-3 text-body-sm font-black text-foreground">{review.title}</h3>
            <p className="mt-1 text-body-sm text-muted-foreground">{review.text}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

function RelatedProductsSection({
  products,
  Link,
}: {
  products: RelatedProduct[];
  Link: StorefrontLinkComponent;
}) {
  return (
    <section>
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-h2 text-foreground">Похожие товары</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">Дополните корзину товарами, которые часто покупают вместе.</p>
        </div>
        <Link
          className="focus-ring inline-flex min-h-[var(--control-height-md)] items-center justify-center rounded-md border border-border-strong bg-surface px-4 text-button font-bold text-foreground shadow-sm transition hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
          href="/catalog"
        >
          Перейти в каталог
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {products.map((product) => (
          <Link
            className="group rounded-lg border border-border bg-surface p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-primary-border hover:shadow-card-hover"
            href={product.href}
            key={product.id}
          >
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              <img
                alt={product.title}
                className="h-full w-full object-cover transition duration-300 ease-product group-hover:scale-[1.03]"
                loading="lazy"
                src={product.imageUrl}
              />
            </div>
            <div className="pt-3">
              <p className="min-h-[40px] overflow-hidden text-body-sm font-black text-foreground group-hover:text-primary-active">
                {product.title}
              </p>
              <div className="mt-3 flex items-end justify-between gap-2">
                <p className="text-h4 text-foreground">
                  {formatPrice(product.price)}
                  <span className="ml-1 text-caption font-semibold text-muted-foreground">/{product.unit}</span>
                </p>
                <span className="text-caption font-bold text-warning">★ {product.rating}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

function ProductDetailsSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("grid gap-6", className)}>
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <Card className="grid gap-4 p-4 lg:grid-cols-[88px_minmax(0,1fr)]" variant="surface">
          <div className="flex gap-2 lg:grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton className="h-20 w-20" key={index} />
            ))}
          </div>
          <Skeleton className="aspect-square w-full" />
        </Card>
        <Card className="p-5" variant="surface">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="mt-4 h-10 w-5/6" />
          <SkeletonText className="mt-4" lines={4} />
          <Skeleton className="mt-5 h-32 w-full" />
          <Skeleton className="mt-5 h-12 w-full" />
        </Card>
      </section>
    </div>
  );
}

function formatPrice(value: number) {
  return currencyFormatter.format(value);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

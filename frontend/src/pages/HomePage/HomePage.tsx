import { Badge } from "../../shared/ui/Badge";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Input } from "../../shared/ui/Input";
import { cn } from "../../shared/lib/cn";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import {
  brands,
  dayProducts,
  deliveryBenefits,
  farmerProducts,
  homePromos,
  newProducts,
  popularCategories,
  recommendations,
  type HomeBenefit,
  type HomeBrand,
  type HomeCategory,
  type HomeProduct,
  type HomePromoTile,
} from "./home-page.mock";

export interface HomePageData {
  promos: HomePromoTile[];
  categories: HomeCategory[];
  dayProducts: HomeProduct[];
  newProducts: HomeProduct[];
  recommendations: HomeProduct[];
  farmerProducts: HomeProduct[];
  brands: HomeBrand[];
  deliveryBenefits: HomeBenefit[];
}

export interface HomePageProps {
  data?: Partial<HomePageData>;
  LinkComponent?: StorefrontLinkComponent;
  onAddToCart?: (product: HomeProduct) => void;
  className?: string;
}

const defaultHomeData: HomePageData = {
  promos: homePromos,
  categories: popularCategories,
  dayProducts,
  newProducts,
  recommendations,
  farmerProducts,
  brands,
  deliveryBenefits,
};

export function HomePage({ data, LinkComponent, onAddToCart, className }: HomePageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const homeData: HomePageData = {
    promos: data?.promos ?? defaultHomeData.promos,
    categories: data?.categories ?? defaultHomeData.categories,
    dayProducts: data?.dayProducts ?? defaultHomeData.dayProducts,
    newProducts: data?.newProducts ?? defaultHomeData.newProducts,
    recommendations: data?.recommendations ?? defaultHomeData.recommendations,
    farmerProducts: data?.farmerProducts ?? defaultHomeData.farmerProducts,
    brands: data?.brands ?? defaultHomeData.brands,
    deliveryBenefits: data?.deliveryBenefits ?? defaultHomeData.deliveryBenefits,
  };

  return (
    <div className={cn("grid gap-8 pb-4", className)}>
      <PromoBoard promos={homeData.promos} Link={Link} />

      <CategorySection categories={homeData.categories} Link={Link} />

      <ProductCarousel
        eyebrow="Товары дня"
        title="Цена ниже до полуночи"
        description="Собрали продукты с высокой оборачиваемостью, свежими поставками и понятной выгодой."
        products={homeData.dayProducts}
        Link={Link}
        onAddToCart={onAddToCart}
      />

      <ProductCarousel
        eyebrow="Новинки"
        title="Новые продукты на полке"
        description="Свежие SKU, сезонные вкусы и товары, которые только появились в каталоге."
        products={homeData.newProducts}
        Link={Link}
        onAddToCart={onAddToCart}
      />

      <CommercialStrip Link={Link} />

      <ProductCarousel
        eyebrow="Рекомендации"
        title="Часто берут вместе"
        description="Быстрый способ собрать корзину для завтраков, ужинов и рабочих перекусов."
        products={homeData.recommendations}
        Link={Link}
        onAddToCart={onAddToCart}
      />

      <FarmerProductsSection products={homeData.farmerProducts} Link={Link} onAddToCart={onAddToCart} />

      <BrandSection brands={homeData.brands} Link={Link} />

      <DeliveryBenefitsSection benefits={homeData.deliveryBenefits} />

      <NewsletterSection />
    </div>
  );
}

function PromoBoard({ promos, Link }: { promos: HomePromoTile[]; Link: StorefrontLinkComponent }) {
  const [primaryPromo, ...secondaryPromos] = promos;

  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.85fr)]" aria-label="Промо">
      {primaryPromo ? (
        <PromoTile promo={primaryPromo} Link={Link} className="min-h-[340px]" />
      ) : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
        {secondaryPromos.map((promo) => (
          <PromoTile key={promo.id} promo={promo} Link={Link} compact />
        ))}
      </div>
    </section>
  );
}

function PromoTile({
  promo,
  Link,
  compact = false,
  className,
}: {
  promo: HomePromoTile;
  Link: StorefrontLinkComponent;
  compact?: boolean;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-lg border border-primary-border bg-primary-soft p-5 shadow-sm",
        compact ? "min-h-[162px]" : "min-h-[300px] p-6",
        className,
      )}
    >
      <img
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        loading={compact ? "lazy" : "eager"}
        src={promo.imageUrl}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-white via-white/[0.86] to-white/[0.18]" />
      <div className={cn("relative z-10 flex h-full max-w-[560px] flex-col justify-between", compact && "max-w-[320px]")}>
        <div>
          <Badge variant="primary">GreenMart</Badge>
          <h1 className={cn("mt-4 font-display text-h1 text-foreground", compact && "text-h3")}>{promo.title}</h1>
          <p className={cn("mt-3 max-w-md text-body text-muted-foreground", compact && "text-body-sm")}>
            {promo.description}
          </p>
        </div>
        <div className="mt-6">
          <Link
            className="focus-ring inline-flex min-h-[var(--control-height-lg)] items-center justify-center rounded-md bg-primary px-5 text-button-lg font-bold text-primary-foreground shadow-sm transition hover:bg-primary-hover"
            href={promo.href}
          >
            {promo.cta}
          </Link>
        </div>
      </div>
    </section>
  );
}

function CategorySection({ categories, Link }: { categories: HomeCategory[]; Link: StorefrontLinkComponent }) {
  return (
    <section>
      <SectionHeader
        actionHref="/catalog"
        actionLabel="Весь каталог"
        description="Плитки помогают быстро перейти в основные продуктовые группы."
        Link={Link}
        title="Популярные категории"
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {categories.map((category) => (
          <Link
            className="group overflow-hidden rounded-lg border border-border bg-surface shadow-sm transition hover:-translate-y-0.5 hover:border-primary-border hover:shadow-card-hover"
            href={category.href}
            key={category.id}
          >
            <div className="flex min-h-[132px] items-center gap-4 p-4">
              <div className="min-w-0 flex-1">
                <Badge variant={category.tone}>{category.itemCount} товаров</Badge>
                <h3 className="mt-3 text-h4 text-foreground group-hover:text-primary-active">{category.title}</h3>
                <p className="mt-1 text-body-sm text-muted-foreground">Свежие позиции каждый день</p>
              </div>
              <img
                alt={category.title}
                className="h-24 w-24 shrink-0 rounded-md object-cover"
                loading="lazy"
                src={category.imageUrl}
              />
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

function ProductCarousel({
  eyebrow,
  title,
  description,
  products,
  Link,
  onAddToCart,
}: {
  eyebrow: string;
  title: string;
  description: string;
  products: HomeProduct[];
  Link: StorefrontLinkComponent;
  onAddToCart?: (product: HomeProduct) => void;
}) {
  return (
    <section>
      <SectionHeader actionHref="/catalog" actionLabel="Смотреть все" description={description} eyebrow={eyebrow} Link={Link} title={title} />
      <div className="-mx-4 overflow-x-auto px-4 pb-2 scrollbar-soft sm:-mx-5 sm:px-5 lg:mx-0 lg:px-0">
        <div className="grid auto-cols-[minmax(220px,240px)] grid-flow-col gap-3 lg:auto-cols-[minmax(220px,1fr)]">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} Link={Link} onAddToCart={onAddToCart} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ProductCard({
  product,
  Link,
  onAddToCart,
}: {
  product: HomeProduct;
  Link: StorefrontLinkComponent;
  onAddToCart?: (product: HomeProduct) => void;
}) {
  return (
    <Card className="flex h-full min-h-[360px] flex-col overflow-hidden p-3" interactive variant="product">
      <Link className="group block" href={product.href}>
        <div className="relative aspect-square overflow-hidden rounded-md bg-muted">
          <img
            alt={product.title}
            className="h-full w-full object-cover transition duration-300 ease-product group-hover:scale-[1.03]"
            loading="lazy"
            src={product.imageUrl}
          />
          {product.badge ? (
            <Badge className="absolute left-2 top-2" variant={product.badgeVariant ?? "primary"}>
              {product.badge}
            </Badge>
          ) : null}
        </div>
      </Link>
      <div className="flex flex-1 flex-col pt-3">
        <div className="flex items-center justify-between gap-2 text-caption text-muted-foreground">
          <span className="truncate">{product.category}</span>
          <span className="font-bold text-warning">★ {product.rating}</span>
        </div>
        <Link className="mt-2 max-h-[44px] min-h-[44px] overflow-hidden text-body-sm font-bold text-foreground hover:text-primary-active" href={product.href}>
          {product.title}
        </Link>
        <div className="mt-auto pt-3">
          <div className="flex items-end justify-between gap-2">
            <div>
              <p className="text-h4 text-foreground">
                {product.price}
                <span className="ml-1 text-caption font-semibold text-muted-foreground">/{product.unit}</span>
              </p>
              {product.oldPrice ? <p className="text-caption text-muted-foreground line-through">{product.oldPrice}</p> : null}
            </div>
          </div>
          <Button className="mt-3" fullWidth onClick={() => onAddToCart?.(product)} variant="primary">
            В корзину
          </Button>
        </div>
      </div>
    </Card>
  );
}

function CommercialStrip({ Link }: { Link: StorefrontLinkComponent }) {
  return (
    <section className="grid gap-3 md:grid-cols-3">
      <InfoTile title="Скидки до 35%" description="На продукты для завтрака" href="/promotions/breakfast" Link={Link} />
      <InfoTile title="Готовая корзина" description="Наборы на 3 дня без лишнего выбора" href="/catalog/sets" Link={Link} />
      <InfoTile title="Premium selection" description="Деликатесы, сыры, рыба и кофе" href="/catalog/premium" Link={Link} />
    </section>
  );
}

function InfoTile({
  title,
  description,
  href,
  Link,
}: {
  title: string;
  description: string;
  href: string;
  Link: StorefrontLinkComponent;
}) {
  return (
    <Link
      className="rounded-lg border border-primary-border bg-primary-soft p-5 text-foreground shadow-sm transition hover:-translate-y-0.5 hover:bg-surface hover:shadow-card-hover"
      href={href}
    >
      <p className="text-h4">{title}</p>
      <p className="mt-2 text-body-sm text-muted-foreground">{description}</p>
    </Link>
  );
}

function FarmerProductsSection({
  products,
  Link,
  onAddToCart,
}: {
  products: HomeProduct[];
  Link: StorefrontLinkComponent;
  onAddToCart?: (product: HomeProduct) => void;
}) {
  return (
    <section className="rounded-lg border border-success-border bg-success-soft p-5">
      <SectionHeader
        actionHref="/catalog/farm"
        actionLabel="Фермерский раздел"
        description="Товары небольших хозяйств с понятным происхождением и короткой логистикой."
        eyebrow="Фермерские продукты"
        Link={Link}
        title="Поставка с фермы"
      />
      <div className="grid gap-3 md:grid-cols-3">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} Link={Link} onAddToCart={onAddToCart} />
        ))}
      </div>
    </section>
  );
}

function BrandSection({ brands, Link }: { brands: HomeBrand[]; Link: StorefrontLinkComponent }) {
  return (
    <section>
      <SectionHeader
        actionHref="/brands"
        actionLabel="Все бренды"
        description="Брендовые полки ускоряют закупку привычных продуктов."
        Link={Link}
        title="Товары по брендам"
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {brands.map((brand) => (
          <Link
            className="group overflow-hidden rounded-lg border border-border bg-surface shadow-sm transition hover:-translate-y-0.5 hover:border-primary-border hover:shadow-card-hover"
            href={brand.href}
            key={brand.id}
          >
            <div className="relative aspect-[4/3] overflow-hidden bg-muted">
              <img
                alt={brand.title}
                className="h-full w-full object-cover transition duration-300 ease-product group-hover:scale-[1.03]"
                loading="lazy"
                src={brand.imageUrl}
              />
              {brand.badge ? <Badge className="absolute left-3 top-3" variant="primary">{brand.badge}</Badge> : null}
            </div>
            <div className="p-4">
              <h3 className="text-h4 text-foreground group-hover:text-primary-active">{brand.title}</h3>
              <p className="mt-1 text-body-sm text-muted-foreground">{brand.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

function DeliveryBenefitsSection({ benefits }: { benefits: HomeBenefit[] }) {
  return (
    <section>
      <SectionHeader
        description="Сервисные преимущества, которые важны именно для продуктового заказа."
        title="Преимущества доставки"
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {benefits.map((benefit, index) => (
          <Card className="p-5" key={benefit.id} variant="surface">
            <span className="grid h-10 w-10 place-items-center rounded-md bg-primary-soft text-button-lg font-black text-primary-active">
              {index + 1}
            </span>
            <h3 className="mt-4 text-h4 text-foreground">{benefit.title}</h3>
            <p className="mt-2 text-body-sm text-muted-foreground">{benefit.description}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}

function NewsletterSection() {
  return (
    <section className="rounded-lg border border-primary-border bg-primary-soft p-5 shadow-sm md:p-6">
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(320px,420px)] md:items-center">
        <div>
          <Badge variant="success">Newsletter</Badge>
          <h2 className="mt-3 text-h2 text-foreground">Получайте лучшие цены до начала распродажи</h2>
          <p className="mt-2 max-w-2xl text-body text-muted-foreground">
            Подборки товаров дня, сезонные фермерские поставки и персональные промокоды.
          </p>
        </div>
        <form action="/subscribe" className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]" method="post">
          <Input aria-label="Email для подписки" inputSize="lg" name="email" placeholder="Введите email" type="email" />
          <Button size="lg" type="submit">
            Подписаться
          </Button>
        </form>
      </div>
    </section>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
  actionHref,
  actionLabel,
  Link,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actionHref?: string;
  actionLabel?: string;
  Link?: StorefrontLinkComponent;
}) {
  return (
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow ? <p className="mb-1 text-caption font-black uppercase text-primary-active">{eyebrow}</p> : null}
        <h2 className="text-h2 text-foreground">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-body-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actionHref && actionLabel && Link ? (
        <Link
          className="focus-ring inline-flex min-h-[var(--control-height-md)] shrink-0 items-center justify-center rounded-md border border-border-strong bg-surface px-4 text-button font-bold text-foreground shadow-sm transition hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
          href={actionHref}
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}

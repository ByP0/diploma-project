import { useEffect, useRef, useState, type FormEvent } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@features/auth/model/useAuth";
import { catalogApi } from "@features/catalog/api/catalogApi";
import { supportApi } from "@features/support/api/supportApi";
import { useCart } from "@features/cart/model/useCart";
import { isApiError, type CategoryRead } from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { canAccess, type AccessRule } from "@shared/lib/access/access";
import { Icon } from "@shared/ui/Icon";
import "./AppLayout.css";

type NavigationItem = {
  access?: AccessRule;
  label: string;
  to: (typeof AppRoutes)[keyof typeof AppRoutes];
};

type WidgetMessage = {
  author: "ai" | "customer";
  body: string;
  id: string;
};

const navigationItems: readonly NavigationItem[] = [
  { to: AppRoutes.home, label: "Главная" },
  {
    to: AppRoutes.admin,
    label: "Админ",
    access: {
      permissions: ["manage_inventory", "manage_orders", "manage_users", "view_login_audit"],
      roles: ["admin"],
    },
  },
];

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Запрос не выполнен.";
}

function createWidgetMessage(author: WidgetMessage["author"], body: string): WidgetMessage {
  return {
    author,
    body,
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  };
}

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout, user } = useAuth();
  const { totalItems } = useCart();
  const [categories, setCategories] = useState<CategoryRead[]>([]);
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [search, setSearch] = useState("");
  const catalogRef = useRef<HTMLDivElement | null>(null);

  const availableItems = navigationItems.filter((item) => canAccess(user, item.access));

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    setSearch(params.get("search") ?? "");
  }, [location.search]);

  useEffect(() => {
    const controller = new AbortController();

    catalogApi
      .getCategories({ signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          setCategories(payload);
        }
      })
      .catch(() => undefined);

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (catalogRef.current && !catalogRef.current.contains(event.target as Node)) {
        setIsCatalogOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  const openHomeWithParams = (entries: Record<string, string | undefined>) => {
    const params = new URLSearchParams();

    for (const [key, value] of Object.entries(entries)) {
      if (value) {
        params.set(key, value);
      }
    }

    const query = params.toString();

    navigate({
      pathname: AppRoutes.home,
      search: query ? `?${query}` : "",
    });
  };

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    openHomeWithParams({
      category: new URLSearchParams(location.search).get("category") ?? undefined,
      search: search.trim() || undefined,
    });
  };

  const handleCategorySelect = (categoryId?: number) => {
    setIsCatalogOpen(false);
    openHomeWithParams({
      category: categoryId ? String(categoryId) : undefined,
      search: search.trim() || undefined,
    });
  };

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate(AppRoutes.login, { replace: true });
    }
  };

  return (
    <div className="shop-layout">
      <header className="shop-header">
        <div className="shop-header__inner">
          <NavLink className="shop-brand" to={AppRoutes.home}>
            <span className="shop-brand__mark" aria-hidden="true">
              ЗЛ
            </span>
            <span>
              Зеленая Лавка
              <small>продуктовый магазин</small>
            </span>
          </NavLink>

          <form className="shop-search" onSubmit={handleSearchSubmit}>
            <Icon name="search" size={19} />
            <input
              aria-label="Поиск по сайту"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Найти продукты, бренды, артикулы"
              value={search}
            />
            <button type="submit">Найти</button>
          </form>

          <div className="shop-catalog" ref={catalogRef}>
            <button
              aria-expanded={isCatalogOpen}
              className="shop-catalog__button"
              onClick={() => setIsCatalogOpen((current) => !current)}
              type="button"
            >
              <Icon name="catalog" size={19} />
              <span>Каталог</span>
              <Icon name="chevron-down" size={17} />
            </button>
            {isCatalogOpen ? (
              <div className="shop-catalog__menu" role="menu">
                <button onClick={() => handleCategorySelect()} role="menuitem" type="button">
                  Все продукты
                </button>
                {categories.map((category) => (
                  <button key={category.id} onClick={() => handleCategorySelect(category.id)} role="menuitem" type="button">
                    {category.name}
                  </button>
                ))}
                {!categories.length ? <span>Категории пока не загружены</span> : null}
              </div>
            ) : null}
          </div>

          <div className="shop-actions">
            <NavLink aria-label="Корзина" className="shop-actions__icon" to={AppRoutes.cart}>
              <Icon name="cart" size={22} />
              <span>{totalItems}</span>
            </NavLink>
            <NavLink className="shop-actions__account" to={isAuthenticated ? AppRoutes.profile : AppRoutes.login}>
              <Icon name="user" size={20} />
              <span>{isAuthenticated ? "Кабинет" : "Войти"}</span>
            </NavLink>
            {isAuthenticated ? (
              <button aria-label="Выйти" className="shop-actions__logout" onClick={handleLogout} type="button">
                <Icon name="logout" size={18} />
              </button>
            ) : null}
          </div>
        </div>

        <nav className="shop-nav" aria-label="Основная навигация">
          {availableItems.map((item) => (
            <NavLink end={item.to === AppRoutes.home} key={item.to} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="shop-main">
        <Outlet />
      </main>

      <SupportChatWidget />
    </div>
  );
}

function SupportChatWidget() {
  const { isAuthenticated, user } = useAuth();
  const [contactEmail, setContactEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<WidgetMessage[]>([
    createWidgetMessage("ai", "Здравствуйте! Я помогу с товарами, заказом, доставкой или оплатой."),
  ]);
  const [ticketId, setTicketId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.email) {
      setContactEmail(user.email);
    }
  }, [user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedMessage = message.trim();
    if (!normalizedMessage) {
      return;
    }

    setMessages((current) => [...current, createWidgetMessage("customer", normalizedMessage)]);
    setMessage("");
    setIsSending(true);
    setError(null);

    try {
      const response = await supportApi.sendChatMessage({
        contact_email: isAuthenticated ? null : contactEmail.trim() || null,
        message: normalizedMessage,
        ticket_id: ticketId,
      });

      setTicketId(response.ticket_id);
      setMessages((current) => [...current, createWidgetMessage("ai", response.answer)]);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className={isOpen ? "support-widget is-open" : "support-widget"} aria-label="Чат поддержки">
      {isOpen ? (
        <section className="support-widget__panel">
          <header>
            <div>
              <strong>Поддержка</strong>
              <span>AI-консультант онлайн</span>
            </div>
            <button aria-label="Закрыть чат" onClick={() => setIsOpen(false)} type="button">
              <Icon name="close" size={18} />
            </button>
          </header>

          <div className="support-widget__messages">
            {messages.map((item) => (
              <article className={item.author === "customer" ? "is-customer" : undefined} key={item.id}>
                <p>{item.body}</p>
              </article>
            ))}
            {error ? <p className="support-widget__error">{error}</p> : null}
          </div>

          {!isAuthenticated ? (
            <label className="support-widget__email">
              <span>Email для ответа</span>
              <input
                onChange={(event) => setContactEmail(event.target.value)}
                placeholder="you@example.com"
                type="email"
                value={contactEmail}
              />
            </label>
          ) : null}

          <form className="support-widget__form" onSubmit={handleSubmit}>
            <input
              aria-label="Сообщение в поддержку"
              disabled={isSending}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Напишите вопрос"
              value={message}
            />
            <button aria-label="Отправить" disabled={isSending || !message.trim()} type="submit">
              <Icon name="send" size={18} />
            </button>
          </form>
        </section>
      ) : null}

      <button className="support-widget__toggle" aria-label="Открыть чат поддержки" onClick={() => setIsOpen((current) => !current)} type="button">
        <Icon name="message" size={26} />
      </button>
    </aside>
  );
}

import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@features/auth/model/useAuth";
import { ordersApi } from "@features/orders/api/ordersApi";
import { profileApi } from "@features/profile/api/profileApi";
import { isApiError, type DecimalString, type OrderRead } from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { Button, EmptyState, ErrorState, LoadingState, TextField, useToast } from "@shared/ui";
import { Icon } from "@shared/ui/Icon";
import "./ProfilePage.css";

type AccountTab = "orders" | "payments" | "profile";
type ProfileAction = "avatar" | "avatar-delete" | "password" | "profile";

const avatarMaxSizeBytes = 5 * 1024 * 1024;
const supportedAvatarTypes = new Set(["image/gif", "image/jpeg", "image/png", "image/webp"]);

const profileActionTitles: Record<ProfileAction, string> = {
  avatar: "Аватар обновлен",
  "avatar-delete": "Аватар удален",
  password: "Пароль изменен",
  profile: "Профиль обновлен",
};

const accountTabs: Array<{ icon: "credit-card" | "package" | "user"; id: AccountTab; label: string }> = [
  { id: "profile", label: "Профиль", icon: "user" },
  { id: "orders", label: "История заказов", icon: "package" },
  { id: "payments", label: "Способы оплаты", icon: "credit-card" },
];

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Действие не выполнено.";
}

function formatPrice(value: DecimalString, currency = "RUB") {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return String(value);
  }

  try {
    return new Intl.NumberFormat("ru-RU", {
      currency,
      maximumFractionDigits: 0,
      style: "currency",
    }).format(numberValue);
  } catch {
    return `${numberValue.toFixed(2)} ${currency}`;
  }
}

function formatDate(value: string | null) {
  if (!value) {
    return "не указано";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getStatusLabel(value: string) {
  const labels: Record<string, string> = {
    awaiting_payment: "ожидает оплату",
    cancelled: "отменен",
    created: "создан",
    delivered: "доставлен",
    failed: "ошибка",
    packed: "собран",
    paid: "оплачен",
    partially_refunded: "частичный возврат",
    pending: "ожидает",
    processing: "в работе",
    refunded: "возврат",
    shipped: "в доставке",
    succeeded: "успешно",
  };

  return labels[value] ?? value.replace(/_/g, " ");
}

export function ProfilePage() {
  const navigate = useNavigate();
  const { reloadUser, user } = useAuth();
  const { showToast } = useToast();
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const [action, setAction] = useState<ProfileAction | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isOrdersLoading, setIsOrdersLoading] = useState(false);
  const [name, setName] = useState(user?.name || "");
  const [newPassword, setNewPassword] = useState("");
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [tab, setTab] = useState<AccountTab>("profile");

  useEffect(() => {
    setName(user?.name || "");
  }, [user]);

  const orderSummary = useMemo(
    () => ({
      active: orders.filter((order) => !["cancelled", "delivered", "failed", "refunded"].includes(order.status)).length,
      total: orders.length,
      totalAmount: orders.reduce((sum, order) => sum + (Number(order.total_amount) || 0), 0),
    }),
    [orders],
  );

  const loadOrders = async (signal?: AbortSignal) => {
    setIsOrdersLoading(true);
    setOrdersError(null);

    try {
      const payload = await ordersApi.list({ limit: 20, offset: 0, signal });
      setOrders(payload);
    } catch (caughtError) {
      if (!signal?.aborted) {
        setOrdersError(getErrorMessage(caughtError));
      }
    } finally {
      if (!signal?.aborted) {
        setIsOrdersLoading(false);
      }
    }
  };

  useEffect(() => {
    if (tab !== "orders") {
      return undefined;
    }

    const controller = new AbortController();
    void loadOrders(controller.signal);
    return () => controller.abort();
  }, [tab]);

  const runProfileAction = async (nextAction: ProfileAction, callback: () => Promise<void>) => {
    setAction(nextAction);
    setError(null);

    try {
      await callback();
      await reloadUser();
      showToast({
        title: profileActionTitles[nextAction],
        variant: "success",
      });
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (name.trim().length < 2) {
      setError("Имя должно содержать минимум 2 символа.");
      return;
    }

    await runProfileAction("profile", async () => {
      await profileApi.updateProfile({ name: name.trim() });
    });
  };

  const handlePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (newPassword.length < 8) {
      setError("Новый пароль должен содержать минимум 8 символов.");
      return;
    }

    if (newPassword !== passwordConfirm) {
      setError("Подтверждение пароля не совпадает.");
      return;
    }

    await runProfileAction("password", async () => {
      await profileApi.updateProfile({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setPasswordConfirm("");
    });
  };

  const handleAvatarChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";

    if (!file) {
      return;
    }

    if (!supportedAvatarTypes.has(file.type)) {
      setError("Можно загрузить только JPG, PNG, WebP или GIF.");
      return;
    }

    if (file.size > avatarMaxSizeBytes) {
      setError("Размер аватара не должен превышать 5 МБ.");
      return;
    }

    await runProfileAction("avatar", async () => {
      await profileApi.uploadAvatar(file);
    });
  };

  const handleAvatarDelete = async () => {
    await runProfileAction("avatar-delete", async () => {
      await profileApi.deleteAvatar();
    });
  };

  return (
    <div className="profile-page">
      <section className="profile-hero">
        <div className="profile-avatar">
          {user?.avatar_url ? <img alt="" src={user.avatar_url} /> : <span>{(user?.name || user?.email || "П").slice(0, 1).toUpperCase()}</span>}
        </div>
        <div>
          <span>Личный кабинет</span>
          <h1>{user?.name || "Профиль покупателя"}</h1>
          <p>{user?.email}</p>
        </div>
      </section>

      <nav className="profile-tabs" aria-label="Разделы личного кабинета">
        {accountTabs.map((item) => (
          <button className={tab === item.id ? "is-active" : undefined} key={item.id} onClick={() => setTab(item.id)} type="button">
            <Icon name={item.icon} size={18} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {error ? (
        <ErrorState
          action={
            <Button onClick={() => setError(null)} variant="secondary">
              Закрыть
            </Button>
          }
          description={error}
          title="Не удалось обновить профиль"
        />
      ) : null}

      {tab === "profile" ? (
        <section className="profile-grid">
          <section className="profile-panel profile-avatar-panel">
            <div className="profile-panel__heading">
              <Icon name="user" size={22} />
              <h2>Аватар</h2>
            </div>
            <div className="profile-avatar-panel__preview">
              {user?.avatar_url ? (
                <img alt="" src={user.avatar_url} />
              ) : (
                <span>{(user?.name || user?.email || "П").slice(0, 1).toUpperCase()}</span>
              )}
            </div>
            <input
              accept="image/png,image/jpeg,image/webp,image/gif"
              className="profile-avatar-panel__input"
              onChange={handleAvatarChange}
              ref={avatarInputRef}
              type="file"
            />
            <div className="profile-avatar-panel__actions">
              <Button
                disabled={Boolean(action)}
                isLoading={action === "avatar"}
                leftSlot={<Icon name="plus" size={18} />}
                onClick={() => avatarInputRef.current?.click()}
                type="button"
              >
                Загрузить
              </Button>
              {user?.avatar_url ? (
                <Button
                  disabled={Boolean(action)}
                  isLoading={action === "avatar-delete"}
                  leftSlot={<Icon name="trash" size={18} />}
                  onClick={() => void handleAvatarDelete()}
                  type="button"
                  variant="secondary"
                >
                  Удалить
                </Button>
              ) : null}
            </div>
          </section>

          <form className="profile-panel" onSubmit={handleProfileSubmit}>
            <div className="profile-panel__heading">
              <Icon name="user" size={22} />
              <h2>Профиль</h2>
            </div>
            <TextField autoComplete="name" label="Имя" minLength={2} onChange={(event) => setName(event.target.value)} value={name} />
            <TextField disabled label="Email" readOnly value={user?.email || ""} />
            <Button disabled={Boolean(action)} isLoading={action === "profile"} type="submit">
              Сохранить профиль
            </Button>
          </form>

          <form className="profile-panel" onSubmit={handlePasswordSubmit}>
            <div className="profile-panel__heading">
              <Icon name="user" size={22} />
              <h2>Безопасность</h2>
            </div>
            <TextField
              autoComplete="current-password"
              label="Текущий пароль"
              onChange={(event) => setCurrentPassword(event.target.value)}
              required
              type="password"
              value={currentPassword}
            />
            <TextField
              autoComplete="new-password"
              label="Новый пароль"
              minLength={8}
              onChange={(event) => setNewPassword(event.target.value)}
              required
              type="password"
              value={newPassword}
            />
            <TextField
              autoComplete="new-password"
              label="Повторите новый пароль"
              minLength={8}
              onChange={(event) => setPasswordConfirm(event.target.value)}
              required
              type="password"
              value={passwordConfirm}
            />
            <Button disabled={Boolean(action)} isLoading={action === "password"} type="submit" variant="secondary">
              Обновить пароль
            </Button>
          </form>
        </section>
      ) : null}

      {tab === "orders" ? (
        <section className="profile-orders">
          <div className="profile-orders__summary">
            <article>
              <span>Всего заказов</span>
              <strong>{orderSummary.total}</strong>
            </article>
            <article>
              <span>Активные</span>
              <strong>{orderSummary.active}</strong>
            </article>
            <article>
              <span>Сумма истории</span>
              <strong>{formatPrice(orderSummary.totalAmount)}</strong>
            </article>
          </div>

          {isOrdersLoading ? (
            <LoadingState description="Загружаем историю заказов." title="История заказов" />
          ) : ordersError ? (
            <ErrorState
              action={
                <Button onClick={() => void loadOrders()} variant="secondary">
                  Повторить
                </Button>
              }
              description={ordersError}
              title="История недоступна"
            />
          ) : orders.length ? (
            <div className="profile-order-list">
              {orders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          ) : (
            <EmptyState
              action={
                <Button onClick={() => navigate(AppRoutes.home)} variant="secondary">
                  Перейти к покупкам
                </Button>
              }
              description="После оформления покупки заказ появится в этом разделе."
              title="Заказов пока нет"
            />
          )}
        </section>
      ) : null}

      {tab === "payments" ? (
        <section className="profile-payments">
          <div className="profile-panel profile-payments__intro">
            <div className="profile-panel__heading">
              <Icon name="credit-card" size={22} />
              <h2>Способы оплаты</h2>
            </div>
            <p>
              Здесь будет хранение банковских карт и быстрый выбор оплаты. Сейчас это безопасная заглушка, потому что
              платежный провайдер подключается отдельно.
            </p>
          </div>

          <div className="profile-payment-grid">
            <article>
              <Icon name="credit-card" size={28} />
              <strong>Банковская карта</strong>
              <span>Скоро</span>
            </article>
            <article>
              <Icon name="package" size={28} />
              <strong>Оплата при получении</strong>
              <span>Доступно при оформлении</span>
            </article>
            <article>
              <Icon name="home" size={28} />
              <strong>СБП и кошельки</strong>
              <span>Планируется</span>
            </article>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function OrderCard({ order }: { order: OrderRead }) {
  return (
    <article className="profile-order-card">
      <div>
        <span>Заказ от {formatDate(order.created_at)}</span>
        <strong>{formatPrice(order.total_amount, order.currency)}</strong>
        <p>{order.items.map((item) => `${item.product_name} x${item.quantity}`).join(", ")}</p>
      </div>
      <div className="profile-order-card__status">
        <span>{getStatusLabel(order.status)}</span>
        <span>{getStatusLabel(order.payment_status)}</span>
      </div>
    </article>
  );
}

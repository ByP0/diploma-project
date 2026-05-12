import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@features/auth/model/useAuth";
import { isApiError } from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { Button, TextField } from "@shared/ui";
import { Icon } from "@shared/ui/Icon";
import "./LoginForm.css";

type AuthMode = "login" | "register";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить вход.";
}

export function LoginForm() {
  const location = useLocation();
  const navigate = useNavigate();
  const { error, isAuthenticated, isLoading, login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [mode, setMode] = useState<AuthMode>("login");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [uiError, setUiError] = useState<string | null>(null);

  const from = (location.state as LocationState | null)?.from?.pathname || AppRoutes.profile;

  if (isAuthenticated) {
    return <Navigate replace to={from} />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUiError(null);

    try {
      if (mode === "login") {
        await login({ email, password });
      } else {
        await register({
          email,
          name: name.trim() || null,
          password,
        });
      }

      navigate(from, { replace: true });
    } catch (caughtError) {
      setUiError(getErrorMessage(caughtError));
    }
  };

  const currentError = uiError || error;

  return (
    <div className="login-shell">
      <section className="login-brand-panel" aria-label="Зеленая Лавка">
        <span className="login-brand-panel__mark">ЗЛ</span>
        <div>
          <p>Зеленая Лавка</p>
          <h1>Вход в личный кабинет</h1>
        </div>
      </section>

      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-form__header">
          <span>Аккаунт</span>
          <h2>{mode === "login" ? "Войти" : "Регистрация"}</h2>
          <p>
            {mode === "login"
              ? "Введите email и пароль, чтобы открыть профиль, историю заказов и оформление покупки."
              : "Создайте аккаунт, если еще не покупали в Зеленой Лавке."}
          </p>
        </div>

        <div className="auth-tabs" role="tablist" aria-label="Выбор действия">
          <button
            aria-selected={mode === "login"}
            className="auth-tab"
            onClick={() => {
              setMode("login");
              setUiError(null);
            }}
            role="tab"
            type="button"
          >
            Вход
          </button>
          <button
            aria-selected={mode === "register"}
            className="auth-tab"
            onClick={() => {
              setMode("register");
              setUiError(null);
            }}
            role="tab"
            type="button"
          >
            Регистрация
          </button>
        </div>

        {currentError ? <p className="auth-error">{currentError}</p> : null}

        {mode === "register" ? (
          <TextField
            autoComplete="name"
            label="Имя"
            minLength={2}
            onChange={(event) => setName(event.target.value)}
            placeholder="Иван"
            value={name}
          />
        ) : null}

        <TextField
          autoComplete="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={email}
        />

        <TextField
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          label="Пароль"
          minLength={8}
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />

        <Button isLoading={isLoading} leftSlot={<Icon name="user" size={18} />} type="submit">
          {mode === "login" ? "Войти в кабинет" : "Создать аккаунт"}
        </Button>

        <div className="login-switch">
          {mode === "login" ? (
            <>
              <span>Еще нет аккаунта?</span>
              <button onClick={() => setMode("register")} type="button">
                Зарегистрироваться
              </button>
            </>
          ) : (
            <>
              <span>Уже есть аккаунт?</span>
              <button onClick={() => setMode("login")} type="button">
                Войти
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}

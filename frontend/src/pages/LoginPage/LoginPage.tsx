import * as React from "react";

import { normalizeApiError } from "../../core/api";
import {
  AuthPageShell,
  FormAlert,
  formatLockoutTime,
  getUserRedirect,
  redirectTo,
  useAuth,
  useBruteForceLock,
  validateEmail,
  validatePassword,
  type FieldErrors,
} from "../../features/auth";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import { Button } from "../../shared/ui/Button";
import { Field, FieldError, FieldLabel, Input } from "../../shared/ui/Input";
import { useToast } from "../../shared/ui/Toast";

type LoginField = "email" | "password";

export interface LoginPageProps {
  LinkComponent?: StorefrontLinkComponent;
  redirectOnSuccess?: boolean;
}

export function LoginPage({ LinkComponent, redirectOnSuccess = true }: LoginPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { login } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [errors, setErrors] = React.useState<FieldErrors<LoginField>>({});
  const [formError, setFormError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const lock = useBruteForceLock("login", email);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    if (lock.isLocked) {
      return;
    }

    const nextErrors: FieldErrors<LoginField> = {
      email: validateEmail(email) ?? undefined,
      password: validatePassword(password) ?? undefined,
    };
    setErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      return;
    }

    setSubmitting(true);

    try {
      const user = await login({ email: email.trim().toLowerCase(), password });
      lock.reset();
      toast({
        title: "Вход выполнен",
        description: "Сессия активна, профиль загружен.",
        variant: "success",
      });

      if (redirectOnSuccess) {
        redirectTo(getUserRedirect(user), true);
      }
    } catch (error) {
      lock.registerFailure();
      setFormError(normalizeApiError(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthPageShell
      description="Войдите, чтобы продолжить покупки, управлять заказами и адресами доставки."
      footer={
        <span>
          Нет аккаунта?{" "}
          <Link className="font-bold text-primary-active hover:text-primary-hover" href="/register">
            Зарегистрироваться
          </Link>
        </span>
      }
      LinkComponent={LinkComponent}
      title="Вход"
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        {formError ? <FormAlert>{formError}</FormAlert> : null}
        {lock.isLocked ? (
          <FormAlert variant="warning">Слишком много попыток. Повторите через {formatLockoutTime(lock.remainingMs)}.</FormAlert>
        ) : lock.attempts > 0 ? (
          <FormAlert variant="warning">Осталось попыток: {lock.remainingAttempts}</FormAlert>
        ) : null}

        <Field invalid={Boolean(errors.email)}>
          <FieldLabel htmlFor="login-email">Email</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.email)}
            autoComplete="email"
            id="login-email"
            inputSize="lg"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="buyer@example.com"
            type="email"
            value={email}
          />
          {errors.email ? <FieldError>{errors.email}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.password)}>
          <div className="flex items-center justify-between gap-3">
            <FieldLabel htmlFor="login-password">Пароль</FieldLabel>
            <Link className="text-caption font-bold text-primary-active hover:text-primary-hover" href="/forgot-password">
              Забыли пароль?
            </Link>
          </div>
          <Input
            aria-invalid={Boolean(errors.password)}
            autoComplete="current-password"
            id="login-password"
            inputSize="lg"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введите пароль"
            type="password"
            value={password}
          />
          {errors.password ? <FieldError>{errors.password}</FieldError> : null}
        </Field>

        <Button disabled={lock.isLocked} fullWidth loading={submitting} size="lg" type="submit">
          Войти
        </Button>
      </form>
    </AuthPageShell>
  );
}

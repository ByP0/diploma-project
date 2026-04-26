import * as React from "react";

import { normalizeApiError } from "../../core/api";
import {
  AuthPageShell,
  FormAlert,
  redirectTo,
  useAuth,
  validateEmail,
  validateName,
  validatePassword,
  type FieldErrors,
} from "../../features/auth";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import { Button } from "../../shared/ui/Button";
import { Field, FieldError, FieldHint, FieldLabel, Input } from "../../shared/ui/Input";
import { useToast } from "../../shared/ui/Toast";

type RegisterField = "name" | "email" | "password" | "confirmPassword";

export interface RegisterPageProps {
  LinkComponent?: StorefrontLinkComponent;
  redirectOnSuccess?: boolean;
}

export function RegisterPage({ LinkComponent, redirectOnSuccess = true }: RegisterPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { register } = useAuth();
  const { toast } = useToast();
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [errors, setErrors] = React.useState<FieldErrors<RegisterField>>({});
  const [formError, setFormError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const nextErrors: FieldErrors<RegisterField> = {
      name: validateName(name) ?? undefined,
      email: validateEmail(email) ?? undefined,
      password: validatePassword(password) ?? undefined,
      confirmPassword: password === confirmPassword ? undefined : "Пароли не совпадают",
    };
    setErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      return;
    }

    setSubmitting(true);

    try {
      await register({
        email: email.trim().toLowerCase(),
        name: name.trim() || null,
        password,
      });
      toast({
        title: "Аккаунт создан",
        description: "Теперь войдите с email и паролем.",
        variant: "success",
      });

      if (redirectOnSuccess) {
        redirectTo("/login?registered=1", true);
      }
    } catch (error) {
      setFormError(normalizeApiError(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthPageShell
      description="Создайте профиль для заказов, адресов доставки, избранного и поддержки."
      footer={
        <span>
          Уже есть аккаунт?{" "}
          <Link className="font-bold text-primary-active hover:text-primary-hover" href="/login">
            Войти
          </Link>
        </span>
      }
      LinkComponent={LinkComponent}
      title="Регистрация"
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        {formError ? <FormAlert>{formError}</FormAlert> : null}

        <Field invalid={Boolean(errors.name)}>
          <FieldLabel htmlFor="register-name">Имя</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.name)}
            autoComplete="name"
            id="register-name"
            inputSize="lg"
            onChange={(event) => setName(event.target.value)}
            placeholder="Как к вам обращаться"
            value={name}
          />
          {errors.name ? <FieldError>{errors.name}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.email)}>
          <FieldLabel htmlFor="register-email">Email</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.email)}
            autoComplete="email"
            id="register-email"
            inputSize="lg"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="buyer@example.com"
            type="email"
            value={email}
          />
          {errors.email ? <FieldError>{errors.email}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.password)}>
          <FieldLabel htmlFor="register-password">Пароль</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.password)}
            autoComplete="new-password"
            id="register-password"
            inputSize="lg"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Надёжный пароль"
            type="password"
            value={password}
          />
          <FieldHint>Минимум 8 символов, заглавная и строчная буква, цифра и спецсимвол.</FieldHint>
          {errors.password ? <FieldError>{errors.password}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.confirmPassword)}>
          <FieldLabel htmlFor="register-confirm-password">Повторите пароль</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.confirmPassword)}
            autoComplete="new-password"
            id="register-confirm-password"
            inputSize="lg"
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Повторите пароль"
            type="password"
            value={confirmPassword}
          />
          {errors.confirmPassword ? <FieldError>{errors.confirmPassword}</FieldError> : null}
        </Field>

        <Button fullWidth loading={submitting} size="lg" type="submit">
          Создать аккаунт
        </Button>
      </form>
    </AuthPageShell>
  );
}

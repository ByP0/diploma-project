import * as React from "react";

import { normalizeApiError } from "../../core/api";
import {
  AuthPageShell,
  FormAlert,
  useAuth,
  validatePassword,
  validateToken,
  type FieldErrors,
} from "../../features/auth";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import { Button } from "../../shared/ui/Button";
import { Field, FieldError, FieldHint, FieldLabel, Input } from "../../shared/ui/Input";
import { useToast } from "../../shared/ui/Toast";

type ResetField = "token" | "password" | "confirmPassword";

export interface ResetPasswordPageProps {
  token?: string;
  LinkComponent?: StorefrontLinkComponent;
}

export function ResetPasswordPage({ token: initialToken, LinkComponent }: ResetPasswordPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { resetPassword } = useAuth();
  const { toast } = useToast();
  const [token, setToken] = React.useState(initialToken ?? getQueryParam("token") ?? "");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [errors, setErrors] = React.useState<FieldErrors<ResetField>>({});
  const [formError, setFormError] = React.useState<string | null>(null);
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const nextErrors: FieldErrors<ResetField> = {
      token: validateToken(token) ?? undefined,
      password: validatePassword(password) ?? undefined,
      confirmPassword: password === confirmPassword ? undefined : "Пароли не совпадают",
    };
    setErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      return;
    }

    setSubmitting(true);

    try {
      const response = await resetPassword({
        new_password: password,
        token: token.trim(),
      });
      setSuccessMessage(response.detail);
      toast({
        title: "Пароль обновлён",
        description: "Теперь можно войти с новым паролем.",
        variant: "success",
      });
    } catch (error) {
      setFormError(normalizeApiError(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthPageShell
      description="Введите токен восстановления и новый пароль."
      footer={
        <Link className="font-bold text-primary-active hover:text-primary-hover" href="/login">
          Перейти ко входу
        </Link>
      }
      LinkComponent={LinkComponent}
      title="Новый пароль"
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        {formError ? <FormAlert>{formError}</FormAlert> : null}
        {successMessage ? <FormAlert variant="success">{successMessage}</FormAlert> : null}

        <Field invalid={Boolean(errors.token)}>
          <FieldLabel htmlFor="reset-token">Токен</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.token)}
            id="reset-token"
            inputSize="lg"
            onChange={(event) => setToken(event.target.value)}
            placeholder="Токен из письма"
            value={token}
          />
          {errors.token ? <FieldError>{errors.token}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.password)}>
          <FieldLabel htmlFor="reset-password">Новый пароль</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.password)}
            autoComplete="new-password"
            id="reset-password"
            inputSize="lg"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Новый пароль"
            type="password"
            value={password}
          />
          <FieldHint>Минимум 8 символов, заглавная и строчная буква, цифра и спецсимвол.</FieldHint>
          {errors.password ? <FieldError>{errors.password}</FieldError> : null}
        </Field>

        <Field invalid={Boolean(errors.confirmPassword)}>
          <FieldLabel htmlFor="reset-confirm-password">Повторите пароль</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.confirmPassword)}
            autoComplete="new-password"
            id="reset-confirm-password"
            inputSize="lg"
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Повторите пароль"
            type="password"
            value={confirmPassword}
          />
          {errors.confirmPassword ? <FieldError>{errors.confirmPassword}</FieldError> : null}
        </Field>

        <Button fullWidth loading={submitting} size="lg" type="submit">
          Обновить пароль
        </Button>
      </form>
    </AuthPageShell>
  );
}

function getQueryParam(name: string) {
  if (typeof window === "undefined") {
    return null;
  }

  return new URLSearchParams(window.location.search).get(name);
}

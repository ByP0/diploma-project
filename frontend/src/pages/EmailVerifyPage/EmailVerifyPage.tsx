import * as React from "react";

import { normalizeApiError } from "../../core/api";
import {
  AuthPageShell,
  FormAlert,
  useAuth,
  validateEmail,
  validateToken,
  type FieldErrors,
} from "../../features/auth";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import { Button } from "../../shared/ui/Button";
import { Field, FieldError, FieldHint, FieldLabel, Input } from "../../shared/ui/Input";
import { useToast } from "../../shared/ui/Toast";

type VerifyField = "email" | "token";

export interface EmailVerifyPageProps {
  token?: string;
  LinkComponent?: StorefrontLinkComponent;
}

export function EmailVerifyPage({ token: initialToken, LinkComponent }: EmailVerifyPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { requestEmailVerification, confirmEmailVerification } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = React.useState("");
  const [token, setToken] = React.useState(initialToken ?? getQueryParam("token") ?? "");
  const [errors, setErrors] = React.useState<FieldErrors<VerifyField>>({});
  const [message, setMessage] = React.useState<string | null>(null);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [requesting, setRequesting] = React.useState(false);
  const [confirming, setConfirming] = React.useState(false);

  const handleRequest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setMessage(null);

    const emailError = validateEmail(email);
    setErrors({ email: emailError ?? undefined });

    if (emailError) {
      return;
    }

    setRequesting(true);

    try {
      const response = await requestEmailVerification({ email: email.trim().toLowerCase() });
      setMessage(response.detail);
      toast({
        title: "Запрос отправлен",
        description: "Проверьте почту или используйте тестовый токен.",
        variant: "success",
      });
    } catch (error) {
      setFormError(normalizeApiError(error));
    } finally {
      setRequesting(false);
    }
  };

  const handleConfirm = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setMessage(null);

    const tokenError = validateToken(token);
    setErrors({ token: tokenError ?? undefined });

    if (tokenError) {
      return;
    }

    setConfirming(true);

    try {
      const response = await confirmEmailVerification({ token: token.trim() });
      setMessage(response.detail);
      toast({
        title: "Проверка email",
        description: response.detail,
        variant: "info",
      });
    } catch (error) {
      setFormError(normalizeApiError(error));
    } finally {
      setConfirming(false);
    }
  };

  return (
    <AuthPageShell
      description="В этой версии backend подтверждение email работает как placeholder."
      footer={
        <Link className="font-bold text-primary-active hover:text-primary-hover" href="/account">
          Вернуться в профиль
        </Link>
      }
      LinkComponent={LinkComponent}
      title="Подтверждение email"
    >
      <div className="grid gap-5">
        {formError ? <FormAlert>{formError}</FormAlert> : null}
        {message ? <FormAlert variant="success">{message}</FormAlert> : null}

        <form className="grid gap-4" onSubmit={handleRequest}>
          <Field invalid={Boolean(errors.email)}>
            <FieldLabel htmlFor="verify-email">Email</FieldLabel>
            <Input
              aria-invalid={Boolean(errors.email)}
              autoComplete="email"
              id="verify-email"
              inputSize="lg"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="buyer@example.com"
              type="email"
              value={email}
            />
            {errors.email ? <FieldError>{errors.email}</FieldError> : null}
          </Field>
          <Button loading={requesting} type="submit" variant="secondary">
            Запросить письмо
          </Button>
        </form>

        <form className="grid gap-4 border-t border-border pt-5" onSubmit={handleConfirm}>
          <Field invalid={Boolean(errors.token)}>
            <FieldLabel htmlFor="verify-token">Токен подтверждения</FieldLabel>
            <Input
              aria-invalid={Boolean(errors.token)}
              id="verify-token"
              inputSize="lg"
              onChange={(event) => setToken(event.target.value)}
              placeholder="Тестовый токен"
              value={token}
            />
            <FieldHint>Backend сейчас возвращает placeholder-сообщение для подтверждения email.</FieldHint>
            {errors.token ? <FieldError>{errors.token}</FieldError> : null}
          </Field>
          <Button loading={confirming} type="submit">
            Подтвердить
          </Button>
        </form>
      </div>
    </AuthPageShell>
  );
}

function getQueryParam(name: string) {
  if (typeof window === "undefined") {
    return null;
  }

  return new URLSearchParams(window.location.search).get(name);
}

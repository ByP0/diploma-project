import * as React from "react";

import { normalizeApiError } from "../../core/api";
import {
  AuthPageShell,
  FormAlert,
  useAuth,
  validateEmail,
  type FieldErrors,
} from "../../features/auth";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import { Button } from "../../shared/ui/Button";
import { Field, FieldError, FieldLabel, Input } from "../../shared/ui/Input";
import { useToast } from "../../shared/ui/Toast";

type ForgotField = "email";

export interface ForgotPasswordPageProps {
  LinkComponent?: StorefrontLinkComponent;
}

export function ForgotPasswordPage({ LinkComponent }: ForgotPasswordPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { recoverPassword } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = React.useState("");
  const [errors, setErrors] = React.useState<FieldErrors<ForgotField>>({});
  const [formError, setFormError] = React.useState<string | null>(null);
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const nextErrors: FieldErrors<ForgotField> = {
      email: validateEmail(email) ?? undefined,
    };
    setErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      return;
    }

    setSubmitting(true);

    try {
      const response = await recoverPassword({ email: email.trim().toLowerCase() });
      setSuccessMessage(response.detail);
      toast({
        title: "Запрос принят",
        description: "Если email существует, инструкции будут отправлены.",
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
      description="Введите email, и мы создадим запрос на восстановление пароля."
      footer={
        <Link className="font-bold text-primary-active hover:text-primary-hover" href="/login">
          Вернуться ко входу
        </Link>
      }
      LinkComponent={LinkComponent}
      title="Восстановление пароля"
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        {formError ? <FormAlert>{formError}</FormAlert> : null}
        {successMessage ? <FormAlert variant="success">{successMessage}</FormAlert> : null}

        <Field invalid={Boolean(errors.email)}>
          <FieldLabel htmlFor="forgot-email">Email</FieldLabel>
          <Input
            aria-invalid={Boolean(errors.email)}
            autoComplete="email"
            id="forgot-email"
            inputSize="lg"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="buyer@example.com"
            type="email"
            value={email}
          />
          {errors.email ? <FieldError>{errors.email}</FieldError> : null}
        </Field>

        <Button fullWidth loading={submitting} size="lg" type="submit">
          Отправить инструкции
        </Button>
      </form>
    </AuthPageShell>
  );
}

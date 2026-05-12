import type { ErrorResponse, ValidationErrorItem } from "./types";

export type ApiErrorKind = "auth" | "forbidden" | "rate_limit" | "server" | "unknown" | "validation";

type ApiErrorOptions = {
  cause?: unknown;
  correlationId?: string | null;
  detail: string;
  kind: ApiErrorKind;
  payload?: unknown;
  retryAfter?: number | null;
  status: number;
  validationErrors?: ValidationErrorItem[];
};

export class ApiError extends Error {
  readonly correlationId: string | null;
  readonly detail: string;
  readonly kind: ApiErrorKind;
  readonly payload: unknown;
  readonly retryAfter: number | null;
  readonly status: number;
  readonly validationErrors: ValidationErrorItem[];

  constructor(options: ApiErrorOptions) {
    super(options.detail, { cause: options.cause });
    this.name = "ApiError";
    this.correlationId = options.correlationId ?? null;
    this.detail = options.detail;
    this.kind = options.kind;
    this.payload = options.payload;
    this.retryAfter = options.retryAfter ?? null;
    this.status = options.status;
    this.validationErrors = options.validationErrors ?? [];
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function parseRetryAfter(value: string | null) {
  if (!value) {
    return null;
  }

  const seconds = Number(value);
  if (Number.isFinite(seconds)) {
    return seconds;
  }

  const date = Date.parse(value);
  if (!Number.isNaN(date)) {
    return Math.max(0, Math.ceil((date - Date.now()) / 1000));
  }

  return null;
}

export function normalizeErrorPayload(payload: unknown): ErrorResponse {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const candidate = payload as Partial<ErrorResponse>;

    if (Array.isArray(candidate.detail)) {
      return {
        detail: "Validation failed.",
        errors: candidate.detail.map((error) => {
          const item = error as { loc?: unknown[]; msg?: string; type?: string };

          return {
            error_type: item.type || "validation_error",
            field: Array.isArray(item.loc) ? item.loc.map(String).join(".") : "request",
            message: item.msg || "Invalid value.",
          };
        }),
      };
    }

    return {
      detail: typeof candidate.detail === "string" ? candidate.detail : "Request failed.",
      errors: Array.isArray(candidate.errors) ? candidate.errors : null,
    };
  }

  return {
    detail: "Request failed.",
    errors: null,
  };
}

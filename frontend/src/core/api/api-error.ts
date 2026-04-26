export interface ApiErrorPayload {
  detail?: string | Array<{ loc?: Array<string | number>; msg: string; type?: string }>;
  message?: string;
  code?: string;
}

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | null;

  constructor(message: string, status: number, payload: ApiErrorPayload | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function normalizeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.payload?.detail)) {
      return error.payload.detail.map((item) => item.msg).join(". ");
    }

    return String(error.payload?.detail || error.payload?.message || error.message);
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос";
}

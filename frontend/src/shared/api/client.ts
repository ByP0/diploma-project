import { apiBaseUrl } from "@shared/config/env";
import { readCookie } from "./cookies";
import { CORRELATION_ID_HEADER, createCorrelationId } from "./correlation";
import { ApiError, normalizeErrorPayload, parseRetryAfter } from "./errors";
import type { ApiMethod, ApiPath, ApiPaths, ApiRequestBody, ApiResponseBody } from "./types";

const CSRF_COOKIE_NAME = "csrf_token";
const CSRF_HEADER_NAME = "X-CSRF-Token";
const REFRESH_PATH = "/auth/refresh";
const UNSAFE_METHODS = new Set<ApiMethod>(["delete", "patch", "post", "put"]);
const BODYLESS_STATUS_CODES = new Set([101, 204, 205, 304]);

type QueryValue = boolean | null | number | string | undefined;
type QueryParams = Record<string, QueryValue | QueryValue[]>;
type PathParams = Record<string, number | string>;

type RequestOptions<TBody> = {
  body?: TBody;
  headers?: HeadersInit;
  pathParams?: PathParams;
  query?: QueryParams;
  signal?: AbortSignal;
  skipAuthRefresh?: boolean;
};

type RequestMeta = {
  correlationId: string;
  responseCorrelationId: string | null;
};

type PathWithMethod<TMethod extends ApiMethod> = {
  [TPath in ApiPath]: TMethod extends keyof ApiPaths[TPath] ? TPath : never;
}[ApiPath];

type MethodFor<TPath extends ApiPath, TMethod extends ApiMethod> = Extract<TMethod, keyof ApiPaths[TPath]>;

export type ApiClientOptions = {
  baseUrl?: string;
};

export class ApiClient {
  readonly baseUrl: string;
  lastCorrelationId: string | null = null;
  private refreshPromise: Promise<void> | null = null;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl ?? apiBaseUrl);
  }

  get<TPath extends PathWithMethod<"get">>(
    path: TPath,
    options?: Omit<RequestOptions<undefined>, "body">,
  ): Promise<ApiResponseBody<TPath, MethodFor<TPath, "get">>> {
    return this.request(path, "get" as MethodFor<TPath, "get">, options as never);
  }

  post<TPath extends PathWithMethod<"post">>(
    path: TPath,
    body: ApiRequestBody<TPath, MethodFor<TPath, "post">>,
    options?: Omit<RequestOptions<typeof body>, "body">,
  ): Promise<ApiResponseBody<TPath, MethodFor<TPath, "post">>> {
    return this.request(path, "post" as MethodFor<TPath, "post">, { ...options, body } as never);
  }

  put<TPath extends PathWithMethod<"put">>(
    path: TPath,
    body: ApiRequestBody<TPath, MethodFor<TPath, "put">>,
    options?: Omit<RequestOptions<typeof body>, "body">,
  ): Promise<ApiResponseBody<TPath, MethodFor<TPath, "put">>> {
    return this.request(path, "put" as MethodFor<TPath, "put">, { ...options, body } as never);
  }

  patch<TPath extends PathWithMethod<"patch">>(
    path: TPath,
    body: ApiRequestBody<TPath, MethodFor<TPath, "patch">>,
    options?: Omit<RequestOptions<typeof body>, "body">,
  ): Promise<ApiResponseBody<TPath, MethodFor<TPath, "patch">>> {
    return this.request(path, "patch" as MethodFor<TPath, "patch">, { ...options, body } as never);
  }

  delete<TPath extends PathWithMethod<"delete">>(
    path: TPath,
    options?: Omit<RequestOptions<undefined>, "body">,
  ): Promise<ApiResponseBody<TPath, MethodFor<TPath, "delete">>> {
    return this.request(path, "delete" as MethodFor<TPath, "delete">, options as never);
  }

  async request<TPath extends ApiPath, TMethod extends keyof ApiPaths[TPath] & ApiMethod>(
    path: TPath,
    method: TMethod,
    options: RequestOptions<ApiRequestBody<TPath, TMethod>> = {},
  ): Promise<ApiResponseBody<TPath, TMethod>> {
    return this.performRequest(path, method, options, false);
  }

  private async performRequest<TPath extends ApiPath, TMethod extends keyof ApiPaths[TPath] & ApiMethod>(
    path: TPath,
    method: TMethod,
    options: RequestOptions<ApiRequestBody<TPath, TMethod>>,
    isRetry: boolean,
  ): Promise<ApiResponseBody<TPath, TMethod>> {
    const correlationId = createCorrelationId();
    const response = await fetch(this.buildUrl(path, options), {
      body: serializeBody(options.body),
      credentials: "include",
      headers: this.buildHeaders(method, correlationId, options),
      method: method.toUpperCase(),
      signal: options.signal,
    });

    const meta: RequestMeta = {
      correlationId,
      responseCorrelationId: response.headers.get(CORRELATION_ID_HEADER),
    };
    this.lastCorrelationId = meta.responseCorrelationId ?? meta.correlationId;

    if (response.status === 401 && !isRetry && !options.skipAuthRefresh && path !== REFRESH_PATH) {
      await this.refreshSession();
      return this.performRequest(path, method, options, true);
    }

    if (!response.ok) {
      throw await this.createApiError(response, meta);
    }

    return parseResponse<ApiResponseBody<TPath, TMethod>>(response);
  }

  private async refreshSession() {
    if (!this.refreshPromise) {
      this.refreshPromise = this.performRequest(
        REFRESH_PATH as ApiPath,
        "post" as never,
        { skipAuthRefresh: true } as never,
        true,
      )
        .then(() => undefined)
        .finally(() => {
          this.refreshPromise = null;
        });
    }

    return this.refreshPromise;
  }

  private buildHeaders<TBody>(method: ApiMethod, correlationId: string, options: RequestOptions<TBody>) {
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");
    headers.set(CORRELATION_ID_HEADER, correlationId);

    if (options.body !== undefined && !isFormData(options.body)) {
      headers.set("Content-Type", "application/json");
    }

    if (UNSAFE_METHODS.has(method)) {
      const csrfToken = readCookie(CSRF_COOKIE_NAME);
      if (csrfToken) {
        headers.set(CSRF_HEADER_NAME, csrfToken);
      }
    }

    return headers;
  }

  private buildUrl<TBody>(path: string, options: RequestOptions<TBody>) {
    const origin = typeof window === "undefined" ? "http://localhost" : window.location.origin;
    const url = new URL(`${this.baseUrl}${interpolatePath(path, options.pathParams)}`, origin);

    if (options.query) {
      for (const [key, value] of Object.entries(options.query)) {
        const values = Array.isArray(value) ? value : [value];
        for (const item of values) {
          if (item !== undefined && item !== null) {
            url.searchParams.append(key, String(item));
          }
        }
      }
    }

    return url.toString();
  }

  private async createApiError(response: Response, meta: RequestMeta) {
    const payload = await parseErrorPayload(response);
    const normalizedPayload = normalizeErrorPayload(payload);
    const correlationId = meta.responseCorrelationId ?? meta.correlationId;
    const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));

    if (response.status === 401) {
      return new ApiError({
        correlationId,
        detail: normalizedPayload.detail || "Authentication is required.",
        kind: "auth",
        payload,
        status: response.status,
      });
    }

    if (response.status === 403) {
      return new ApiError({
        correlationId,
        detail: normalizedPayload.detail || "You do not have access to this resource.",
        kind: "forbidden",
        payload,
        status: response.status,
      });
    }

    if (response.status === 422) {
      return new ApiError({
        correlationId,
        detail: normalizedPayload.detail || "Validation failed.",
        kind: "validation",
        payload,
        status: response.status,
        validationErrors: normalizedPayload.errors ?? [],
      });
    }

    if (response.status === 429) {
      return new ApiError({
        correlationId,
        detail: normalizedPayload.detail || "Too many requests.",
        kind: "rate_limit",
        payload,
        retryAfter,
        status: response.status,
      });
    }

    return new ApiError({
      correlationId,
      detail: normalizedPayload.detail || "Request failed.",
      kind: response.status >= 500 ? "server" : "unknown",
      payload,
      status: response.status,
    });
  }
}

export const apiClient = new ApiClient();

function normalizeBaseUrl(value: string) {
  return value.replace(/\/+$/, "");
}

function interpolatePath(path: string, pathParams?: PathParams) {
  if (!pathParams) {
    return path;
  }

  return path.replace(/\{([^}]+)\}/g, (_match, key: string) => {
    const value = pathParams[key];

    if (value === undefined) {
      throw new Error(`Missing API path param: ${key}`);
    }

    return encodeURIComponent(String(value));
  });
}

function serializeBody(body: unknown) {
  if (body === undefined) {
    return undefined;
  }

  if (isFormData(body) || isBlob(body) || typeof body === "string") {
    return body;
  }

  return JSON.stringify(body);
}

function isFormData(value: unknown): value is FormData {
  return typeof FormData !== "undefined" && value instanceof FormData;
}

function isBlob(value: unknown): value is Blob {
  return typeof Blob !== "undefined" && value instanceof Blob;
}

async function parseResponse<TResponse>(response: Response): Promise<TResponse> {
  if (BODYLESS_STATUS_CODES.has(response.status)) {
    return undefined as TResponse;
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as TResponse;
  }

  return response.json() as Promise<TResponse>;
}

async function parseErrorPayload(response: Response) {
  const contentType = response.headers.get("Content-Type") || "";

  if (!contentType.includes("application/json")) {
    const text = await response.text();
    return text ? { detail: text } : { detail: response.statusText };
  }

  try {
    return await response.json();
  } catch {
    return { detail: response.statusText };
  }
}

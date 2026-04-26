import { ApiError, type ApiErrorPayload } from "./api-error";
import { appendCsrfHeader } from "./csrf";

export interface ApiRequestOptions extends Omit<RequestInit, "body" | "headers"> {
  body?: BodyInit | Record<string, unknown> | null;
  headers?: HeadersInit;
  skipAuthRefresh?: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

type AuthRefreshHandler = () => Promise<TokenPair | null>;
type AccessTokenProvider = () => string | null;

let authRefreshHandler: AuthRefreshHandler | null = null;
let accessTokenProvider: AccessTokenProvider | null = null;

export function setAuthRefreshHandler(handler: AuthRefreshHandler | null) {
  authRefreshHandler = handler;
}

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

export function getApiBaseUrl() {
  const env = getRuntimeEnv();
  return env.VITE_API_BASE_URL || "";
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  return requestWithRetry<T>(path, options, false);
}

async function requestWithRetry<T>(path: string, options: ApiRequestOptions, retried: boolean): Promise<T> {
  const response = await fetch(buildUrl(path), buildRequestInit(options));

  if (response.status === 401 && !options.skipAuthRefresh && !retried && authRefreshHandler) {
    const tokenPair = await authRefreshHandler();
    if (tokenPair) {
      return requestWithRetry<T>(path, options, true);
    }
  }

  if (!response.ok) {
    throw await buildApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as T;
  }

  return (await response.json()) as T;
}

function buildRequestInit(options: ApiRequestOptions): RequestInit {
  const requestOptions = { ...options };
  delete requestOptions.skipAuthRefresh;
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers);
  const accessToken = accessTokenProvider?.();

  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  appendCsrfHeader(headers, method);

  let body = options.body as BodyInit | undefined;
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (options.body && !isFormData && typeof options.body !== "string") {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  return {
    ...requestOptions,
    body,
    credentials: "include",
    headers,
    method,
  };
}

function buildUrl(path: string) {
  if (/^https?:\/\//.test(path)) {
    return path;
  }

  const baseUrl = getApiBaseUrl().replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

async function buildApiError(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  let payload: ApiErrorPayload | null = null;

  if (contentType.includes("application/json")) {
    payload = (await response.json().catch(() => null)) as ApiErrorPayload | null;
  }

  const detail = payload?.detail;
  const message = Array.isArray(detail)
    ? detail.map((item) => item.msg).join(". ")
    : String(detail || payload?.message || response.statusText || "Request failed");

  return new ApiError(message, response.status, payload);
}

function getRuntimeEnv(): Record<string, string | undefined> {
  const meta = import.meta as ImportMeta & { env?: Record<string, string | undefined> };
  return meta.env ?? {};
}

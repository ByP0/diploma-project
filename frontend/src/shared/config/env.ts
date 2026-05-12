const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");

export const apiBaseUrl = trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || "/api");
export const apiMocksEnabled = import.meta.env.VITE_API_MOCKS === "true";
export const realtimeUrl = import.meta.env.VITE_REALTIME_URL || "";

import type { TokenPair } from "../../../core/api";

let accessToken: string | null = null;
let refreshToken: string | null = null;
let accessTokenExpiresAt: number | null = null;

export const authTokenStore = {
  getAccessToken() {
    return accessToken;
  },

  getRefreshToken() {
    return refreshToken;
  },

  getAccessTokenExpiresAt() {
    return accessTokenExpiresAt;
  },

  setTokenPair(tokenPair: TokenPair | null) {
    accessToken = tokenPair?.access_token ?? null;
    refreshToken = tokenPair?.refresh_token ?? null;
    accessTokenExpiresAt = tokenPair?.access_token ? decodeJwtExpiration(tokenPair.access_token) : null;
  },

  clear() {
    accessToken = null;
    refreshToken = null;
    accessTokenExpiresAt = null;
  },
};

function decodeJwtExpiration(token: string): number | null {
  try {
    const payloadPart = token.split(".")[1];
    if (!payloadPart) {
      return null;
    }

    const normalizedPayload = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const paddedPayload = normalizedPayload.padEnd(Math.ceil(normalizedPayload.length / 4) * 4, "=");
    const decodedPayload =
      typeof globalThis.atob === "function"
        ? globalThis.atob(paddedPayload)
        : "";
    const payload = JSON.parse(decodedPayload) as { exp?: number };
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

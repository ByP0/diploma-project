import * as React from "react";

import {
  setAccessTokenProvider,
  setAuthRefreshHandler,
  type TokenPair,
} from "../../../core/api";
import { authApi } from "../api";
import type {
  AuthPermission,
  AuthStatus,
  AuthUser,
  EmailVerificationConfirmRequest,
  EmailVerificationRequest,
  LoginRequest,
  MessageResponse,
  PasswordRecoveryRequest,
  PasswordResetRequest,
  RegisterRequest,
  UserRole,
} from "./auth.types";
import { authTokenStore } from "./session-token";

export interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<AuthUser>;
  register: (payload: RegisterRequest) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<TokenPair | null>;
  reloadUser: () => Promise<AuthUser | null>;
  recoverPassword: (payload: PasswordRecoveryRequest) => Promise<MessageResponse>;
  resetPassword: (payload: PasswordResetRequest) => Promise<MessageResponse>;
  requestEmailVerification: (payload: EmailVerificationRequest) => Promise<MessageResponse>;
  confirmEmailVerification: (payload: EmailVerificationConfirmRequest) => Promise<MessageResponse>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  hasPermission: (permission: AuthPermission) => boolean;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = React.useState<AuthStatus>("checking");
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = React.useState<string | null>(authTokenStore.getAccessToken());
  const refreshPromiseRef = React.useRef<Promise<TokenPair | null> | null>(null);

  const refreshSession = React.useCallback(async () => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    refreshPromiseRef.current = authApi
      .refresh()
      .then((tokenPair) => {
        authTokenStore.setTokenPair(tokenPair);
        setAccessToken(authTokenStore.getAccessToken());
        return tokenPair;
      })
      .catch(() => {
        authTokenStore.clear();
        setAccessToken(null);
        setUser(null);
        setStatus("anonymous");
        return null;
      })
      .finally(() => {
        refreshPromiseRef.current = null;
      });

    return refreshPromiseRef.current;
  }, []);

  const reloadUser = React.useCallback(async () => {
    try {
      const currentUser = await authApi.getMe();
      setUser(currentUser);
      setStatus("authenticated");
      return currentUser;
    } catch {
      setUser(null);
      setStatus("anonymous");
      return null;
    }
  }, []);

  React.useEffect(() => {
    setAccessTokenProvider(() => authTokenStore.getAccessToken());
    setAuthRefreshHandler(refreshSession);

    return () => {
      setAccessTokenProvider(null);
      setAuthRefreshHandler(null);
    };
  }, [refreshSession]);

  React.useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      setStatus("checking");

      const currentUser = await authApi.getMe().catch(async () => {
        const tokenPair = await refreshSession();
        if (!tokenPair) {
          return null;
        }
        return authApi.getMe().catch(() => null);
      });

      if (cancelled) {
        return;
      }

      if (currentUser) {
        setUser(currentUser);
        setStatus("authenticated");
      } else {
        setUser(null);
        setStatus("anonymous");
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, [refreshSession]);

  React.useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    const expiresAt = authTokenStore.getAccessTokenExpiresAt();
    const delay = expiresAt ? Math.max(expiresAt - Date.now() - 60_000, 15_000) : 25 * 60 * 1000;
    const timer = globalThis.setTimeout(() => {
      refreshSession();
    }, delay);

    return () => globalThis.clearTimeout(timer);
  }, [accessToken, refreshSession, status]);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      accessToken,
      isAuthenticated: status === "authenticated" && Boolean(user),
      login: async (payload) => {
        const currentUser = await authApi.login(payload);
        setUser(currentUser);
        setStatus("authenticated");

        const tokenPair = await refreshSession();
        if (tokenPair) {
          authTokenStore.setTokenPair(tokenPair);
          setAccessToken(authTokenStore.getAccessToken());
        }

        return currentUser;
      },
      register: (payload) => authApi.register(payload),
      logout: async () => {
        await authApi.logout().catch(() => undefined);
        authTokenStore.clear();
        setAccessToken(null);
        setUser(null);
        setStatus("anonymous");
      },
      refreshSession,
      reloadUser,
      recoverPassword: (payload) => authApi.recoverPassword(payload),
      resetPassword: (payload) => authApi.resetPassword(payload),
      requestEmailVerification: (payload) => authApi.requestEmailVerification(payload),
      confirmEmailVerification: (payload) => authApi.confirmEmailVerification(payload),
      hasRole: (roles) => {
        if (!user) {
          return false;
        }

        return Array.isArray(roles) ? roles.includes(user.role) : user.role === roles;
      },
      hasPermission: (permission) => Boolean(user?.permissions.includes(permission)),
    }),
    [accessToken, refreshSession, reloadUser, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}

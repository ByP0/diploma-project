import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import type { User } from "@entities/user/model";
import { authApi } from "@features/auth/api/authApi";
import type {
  EmailVerificationConfirmInput,
  EmailVerificationRequestInput,
  LoginInput,
  PasswordRecoveryInput,
  PasswordResetInput,
  RegisterInput,
} from "@features/auth/api/authApi";
import { isApiError, type MessageResponse } from "@shared/api";

type AuthStatus = "anonymous" | "authenticated" | "checking";

type AuthContextValue = {
  confirmEmailVerification: (data: EmailVerificationConfirmInput) => Promise<MessageResponse>;
  error: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  isLoading: boolean;
  login: (data: LoginInput) => Promise<User>;
  logout: () => Promise<void>;
  recoverPassword: (data: PasswordRecoveryInput) => Promise<MessageResponse>;
  refresh: () => Promise<User>;
  register: (data: RegisterInput) => Promise<User>;
  reloadUser: () => Promise<User | null>;
  requestEmailVerification: (data: EmailVerificationRequestInput) => Promise<MessageResponse>;
  resetPassword: (data: PasswordResetInput) => Promise<MessageResponse>;
  status: AuthStatus;
  user: User | null;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

type AuthProviderProps = {
  children: ReactNode;
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Authentication request failed.";
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [user, setUser] = useState<User | null>(null);

  const setCurrentUser = useCallback((nextUser: User | null) => {
    setUser(nextUser);
    setStatus(nextUser ? "authenticated" : "anonymous");
  }, []);

  const reloadUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getCurrentUser();
      setError(null);
      setCurrentUser(currentUser);
      return currentUser;
    } catch (caughtError) {
      setCurrentUser(null);

      if (isApiError(caughtError) && caughtError.kind === "auth") {
        setError(null);
        return null;
      }

      setError(getErrorMessage(caughtError));
      return null;
    }
  }, [setCurrentUser]);

  useEffect(() => {
    let isMounted = true;

    authApi
      .getCurrentUser()
      .then((currentUser) => {
        if (isMounted) {
          setError(null);
          setCurrentUser(currentUser);
        }
      })
      .catch((caughtError) => {
        if (!isMounted) {
          return;
        }

        setCurrentUser(null);

        if (isApiError(caughtError) && caughtError.kind === "auth") {
          setError(null);
          return;
        }

        setError(getErrorMessage(caughtError));
      });

    return () => {
      isMounted = false;
    };
  }, [setCurrentUser]);

  const runAuthAction = useCallback(
    async <TResult,>(action: () => Promise<TResult>) => {
      setIsLoading(true);
      setError(null);

      try {
        return await action();
      } catch (caughtError) {
        const message = getErrorMessage(caughtError);
        setError(message);
        throw caughtError;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const login = useCallback(
    (data: LoginInput) =>
      runAuthAction(async () => {
        const currentUser = await authApi.login(data);
        setCurrentUser(currentUser);
        return currentUser;
      }),
    [runAuthAction, setCurrentUser],
  );

  const register = useCallback(
    (data: RegisterInput) =>
      runAuthAction(async () => {
        const currentUser = await authApi.register(data);
        setCurrentUser(currentUser);
        return currentUser;
      }),
    [runAuthAction, setCurrentUser],
  );

  const logout = useCallback(
    () =>
      runAuthAction(async () => {
        try {
          await authApi.logout();
        } finally {
          setCurrentUser(null);
        }
      }),
    [runAuthAction, setCurrentUser],
  );

  const refresh = useCallback(
    () =>
      runAuthAction(async () => {
        const currentUser = await authApi.refresh();
        setCurrentUser(currentUser);
        return currentUser;
      }),
    [runAuthAction, setCurrentUser],
  );

  const recoverPassword = useCallback(
    (data: PasswordRecoveryInput) => runAuthAction(() => authApi.recoverPassword(data)),
    [runAuthAction],
  );

  const resetPassword = useCallback(
    (data: PasswordResetInput) => runAuthAction(() => authApi.resetPassword(data)),
    [runAuthAction],
  );

  const requestEmailVerification = useCallback(
    (data: EmailVerificationRequestInput) => runAuthAction(() => authApi.requestEmailVerification(data)),
    [runAuthAction],
  );

  const confirmEmailVerification = useCallback(
    (data: EmailVerificationConfirmInput) => runAuthAction(() => authApi.confirmEmailVerification(data)),
    [runAuthAction],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      confirmEmailVerification,
      error,
      isAuthenticated: status === "authenticated",
      isInitializing: status === "checking",
      isLoading,
      login,
      logout,
      recoverPassword,
      refresh,
      register,
      reloadUser,
      requestEmailVerification,
      resetPassword,
      status,
      user,
    }),
    [
      confirmEmailVerification,
      error,
      isLoading,
      login,
      logout,
      recoverPassword,
      refresh,
      register,
      reloadUser,
      requestEmailVerification,
      resetPassword,
      status,
      user,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

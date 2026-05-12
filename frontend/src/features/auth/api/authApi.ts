import { apiClient } from "@shared/api";
import type {
  EmailVerificationConfirmStub,
  EmailVerificationStubRequest,
  UserCreate,
  UserLogin,
  UserPasswordRecoveryRequest,
  UserPasswordReset,
} from "@shared/api";

export type RegisterInput = UserCreate;
export type LoginInput = UserLogin;
export type PasswordRecoveryInput = UserPasswordRecoveryRequest;
export type PasswordResetInput = UserPasswordReset;
export type EmailVerificationRequestInput = EmailVerificationStubRequest;
export type EmailVerificationConfirmInput = EmailVerificationConfirmStub;

export const authApi = {
  async getCurrentUser() {
    return apiClient.get("/users/me");
  },

  async login(data: LoginInput) {
    await apiClient.post("/auth/login", data, { skipAuthRefresh: true });
    return authApi.getCurrentUser();
  },

  async register(data: RegisterInput) {
    await apiClient.post("/auth/register", data, { skipAuthRefresh: true });
    await apiClient.post(
      "/auth/login",
      {
        email: data.email,
        password: data.password,
      },
      { skipAuthRefresh: true },
    );
    return authApi.getCurrentUser();
  },

  async logout() {
    return apiClient.post("/auth/logout", undefined, { skipAuthRefresh: true });
  },

  async refresh() {
    await apiClient.post("/auth/refresh", undefined, { skipAuthRefresh: true });
    return authApi.getCurrentUser();
  },

  async recoverPassword(data: PasswordRecoveryInput) {
    return apiClient.post("/auth/password/recover", data, { skipAuthRefresh: true });
  },

  async resetPassword(data: PasswordResetInput) {
    return apiClient.post("/auth/password/reset", data, { skipAuthRefresh: true });
  },

  async requestEmailVerification(data: EmailVerificationRequestInput) {
    return apiClient.post("/auth/email-verification/request", data, { skipAuthRefresh: true });
  },

  async confirmEmailVerification(data: EmailVerificationConfirmInput) {
    return apiClient.post("/auth/email-verification/confirm", data, { skipAuthRefresh: true });
  },
};

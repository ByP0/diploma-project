import { apiRequest, type TokenPair } from "../../../core/api";
import type {
  AuthUser,
  EmailVerificationConfirmRequest,
  EmailVerificationRequest,
  LoginRequest,
  MessageResponse,
  PasswordRecoveryRequest,
  PasswordResetRequest,
  RegisterRequest,
} from "../model/auth.types";

export const authApi = {
  register(payload: RegisterRequest) {
    return apiRequest<AuthUser>("/api/auth/register", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  login(payload: LoginRequest) {
    return apiRequest<AuthUser>("/api/auth/login", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  refresh() {
    return apiRequest<TokenPair>("/api/auth/refresh", {
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  logout() {
    return apiRequest<void>("/api/auth/logout", {
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  getMe() {
    return apiRequest<AuthUser>("/api/users/me");
  },

  recoverPassword(payload: PasswordRecoveryRequest) {
    return apiRequest<MessageResponse>("/api/auth/password/recover", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  resetPassword(payload: PasswordResetRequest) {
    return apiRequest<MessageResponse>("/api/auth/password/reset", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  requestEmailVerification(payload: EmailVerificationRequest) {
    return apiRequest<MessageResponse>("/api/auth/email-verification/request", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },

  confirmEmailVerification(payload: EmailVerificationConfirmRequest) {
    return apiRequest<MessageResponse>("/api/auth/email-verification/confirm", {
      body: payload,
      method: "POST",
      skipAuthRefresh: true,
    });
  },
};

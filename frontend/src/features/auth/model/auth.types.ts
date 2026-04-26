import type { TokenPair } from "../../../core/api";

export type UserRole = "user" | "admin" | "manager" | "support";

export type AuthPermission =
  | "manage_users"
  | "view_login_audit"
  | "manage_inventory"
  | "manage_orders"
  | "view_orders"
  | "manage_payments"
  | "manage_delivery"
  | "manage_notifications"
  | "view_admin_audit"
  | "handle_support";

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  avatar_image_id: string | null;
  avatar_url?: string | null;
  role: UserRole;
  permissions: AuthPermission[];
  is_active: boolean;
  is_blocked: boolean;
  blocked_at: string | null;
  blocked_reason: string | null;
  email_verified_at: string | null;
  is_email_verified?: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string | null;
}

export interface PasswordRecoveryRequest {
  email: string;
}

export interface PasswordResetRequest {
  token: string;
  new_password: string;
}

export interface EmailVerificationRequest {
  email: string;
}

export interface EmailVerificationConfirmRequest {
  token: string;
}

export interface MessageResponse {
  detail: string;
}

export interface AuthSession {
  user: AuthUser;
  tokenPair?: TokenPair | null;
}

export type AuthStatus = "checking" | "authenticated" | "anonymous";

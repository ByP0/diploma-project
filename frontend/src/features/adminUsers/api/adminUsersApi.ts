import { apiClient } from "@shared/api";
import type { UserAdminUpdate, UserLoginAuditRead, UserRead, UserRole, UUID } from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

export type AdminUsersFilters = {
  email_verified?: boolean;
  is_active?: boolean;
  is_blocked?: boolean;
  limit?: number;
  offset?: number;
  role?: UserRole;
  search?: string;
};

export type LoginAuditFilters = {
  created_from?: string;
  created_to?: string;
  email?: string;
  event_type?: string;
  ip_address?: string;
  limit?: number;
  offset?: number;
  success?: boolean;
  user_id?: UUID;
};

export const adminUsersApi = {
  listLoginAudit(filters: LoginAuditFilters = {}, options: RequestOptions = {}): Promise<UserLoginAuditRead[]> {
    return apiClient.get("/users/login-audit", {
      query: {
        created_from: filters.created_from,
        created_to: filters.created_to,
        email: filters.email,
        event_type: filters.event_type,
        ip_address: filters.ip_address,
        limit: filters.limit ?? 100,
        offset: filters.offset ?? 0,
        success: filters.success,
        user_id: filters.user_id,
      },
      signal: options.signal,
    });
  },

  listUsers(filters: AdminUsersFilters = {}, options: RequestOptions = {}): Promise<UserRead[]> {
    return apiClient.get("/users", {
      query: {
        email_verified: filters.email_verified,
        is_active: filters.is_active,
        is_blocked: filters.is_blocked,
        limit: filters.limit ?? 50,
        offset: filters.offset ?? 0,
        role: filters.role,
        search: filters.search,
      },
      signal: options.signal,
    });
  },

  updateUserAccess(userId: UUID, data: UserAdminUpdate): Promise<UserRead> {
    return apiClient.patch("/users/{user_id}/access", data, {
      pathParams: {
        user_id: userId,
      },
    });
  },
};

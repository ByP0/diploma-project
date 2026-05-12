import { apiClient } from "@shared/api";
import type {
  SupportAdminReplyCreate,
  SupportTicketAdminUpdate,
  SupportTicketListResponse,
  SupportTicketPriority,
  SupportTicketRead,
  SupportTicketStatus,
  UUID,
} from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

export type AdminSupportTicketFilters = {
  assigned_admin_id?: UUID;
  human_handoff_requested?: boolean;
  limit?: number;
  offset?: number;
  priority?: SupportTicketPriority;
  search?: string;
  status?: SupportTicketStatus;
};

export const adminSupportApi = {
  getTicket(ticketId: UUID, options: RequestOptions = {}): Promise<SupportTicketRead> {
    return apiClient.get("/support/tickets/admin/{ticket_id}", {
      pathParams: {
        ticket_id: ticketId,
      },
      signal: options.signal,
    });
  },

  listTickets(filters: AdminSupportTicketFilters = {}, options: RequestOptions = {}): Promise<SupportTicketListResponse> {
    return apiClient.get("/support/tickets", {
      query: {
        assigned_admin_id: filters.assigned_admin_id,
        human_handoff_requested: filters.human_handoff_requested,
        limit: filters.limit ?? 50,
        offset: filters.offset ?? 0,
        priority: filters.priority,
        search: filters.search,
        status: filters.status,
      },
      signal: options.signal,
    });
  },

  reply(ticketId: UUID, data: SupportAdminReplyCreate): Promise<SupportTicketRead> {
    return apiClient.post("/support/tickets/{ticket_id}/admin-reply", data, {
      pathParams: {
        ticket_id: ticketId,
      },
    });
  },

  updateTicket(ticketId: UUID, data: SupportTicketAdminUpdate): Promise<SupportTicketRead> {
    return apiClient.patch("/support/tickets/{ticket_id}", data, {
      pathParams: {
        ticket_id: ticketId,
      },
    });
  },
};

import { apiClient } from "@shared/api";
import type { ChatRequest, ChatResponse, SupportTicketListResponse, SupportTicketRead, UUID } from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

type ListTicketsParams = RequestOptions & {
  limit?: number;
  offset?: number;
};

export const supportApi = {
  getTicket(ticketId: UUID, options?: RequestOptions): Promise<SupportTicketRead> {
    return apiClient.get("/support/tickets/me/{ticket_id}", {
      pathParams: {
        ticket_id: ticketId,
      },
      signal: options?.signal,
    });
  },

  listMyTickets(params: ListTicketsParams = {}): Promise<SupportTicketListResponse> {
    return apiClient.get("/support/tickets/me", {
      query: {
        limit: params.limit ?? 20,
        offset: params.offset ?? 0,
      },
      signal: params.signal,
    });
  },

  sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
    return apiClient.post("/chat", data);
  },
};

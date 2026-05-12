import { apiClient } from "@shared/api";
import type { MessageResponse, NotificationMessageRead } from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

export type NotificationMessageFilters = {
  channel?: string;
  limit?: number;
  offset?: number;
  recipient?: string;
  status?: string;
  template_name?: string;
};

export const adminNotificationsApi = {
  listMessages(filters: NotificationMessageFilters = {}, options: RequestOptions = {}): Promise<NotificationMessageRead[]> {
    return apiClient.get("/notifications/messages", {
      query: {
        channel: filters.channel,
        limit: filters.limit ?? 50,
        offset: filters.offset ?? 0,
        recipient: filters.recipient,
        status: filters.status,
        template_name: filters.template_name,
      },
      signal: options.signal,
    });
  },

  processQueue(): Promise<MessageResponse> {
    return apiClient.post("/notifications/process", undefined);
  },
};

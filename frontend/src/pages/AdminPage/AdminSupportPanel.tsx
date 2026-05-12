import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminSupportApi } from "@features/adminSupport/api/adminSupportApi";
import { isApiError } from "@shared/api";
import type {
  SupportMessageRead,
  SupportTicketPriority,
  SupportTicketRead,
  SupportTicketStatus,
  SupportTicketSummary,
  UUID,
} from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, SelectField, TextField, useToast } from "@shared/ui";

const PAGE_SIZE = 50;

const SUPPORT_STATUS_OPTIONS: Array<{ label: string; value: SupportTicketStatus }> = [
  { label: "Open", value: "open" },
  { label: "In progress", value: "in_progress" },
  { label: "Waiting customer", value: "waiting_customer" },
  { label: "Resolved", value: "resolved" },
  { label: "Closed", value: "closed" },
];

const SUPPORT_PRIORITY_OPTIONS: Array<{ label: string; value: SupportTicketPriority }> = [
  { label: "Low", value: "low" },
  { label: "Normal", value: "normal" },
  { label: "High", value: "high" },
  { label: "Urgent", value: "urgent" },
];

const SUPPORT_TRANSITIONS: Record<SupportTicketStatus, SupportTicketStatus[]> = {
  open: ["in_progress", "waiting_customer", "resolved", "closed"],
  in_progress: ["open", "waiting_customer", "resolved", "closed"],
  waiting_customer: ["open", "in_progress", "resolved", "closed"],
  resolved: ["in_progress", "closed"],
  closed: ["in_progress"],
};

type BoolFilter = "all" | "false" | "true";

type SupportFiltersForm = {
  assignedAdminId: string;
  handoff: BoolFilter;
  priority: SupportTicketPriority | "";
  search: string;
  status: SupportTicketStatus | "";
};

const initialFilters: SupportFiltersForm = {
  assignedAdminId: "",
  handoff: "all",
  priority: "",
  search: "",
  status: "",
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Support request failed.";
}

function formatDate(value: string | null) {
  if (!value) {
    return "not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getStatusLabel(value: string) {
  return value.replace(/_/g, " ");
}

function parseBoolFilter(value: BoolFilter) {
  if (value === "all") {
    return undefined;
  }

  return value === "true";
}

type SupportAction = "reply" | "update" | null;

export function AdminSupportPanel() {
  const { showToast } = useToast();
  const [action, setAction] = useState<SupportAction>(null);
  const [assignedAdminId, setAssignedAdminId] = useState("");
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailReloadKey, setDetailReloadKey] = useState(0);
  const [draftFilters, setDraftFilters] = useState<SupportFiltersForm>(initialFilters);
  const [filters, setFilters] = useState<SupportFiltersForm>(initialFilters);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isListLoading, setIsListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [priorityDraft, setPriorityDraft] = useState<SupportTicketPriority>("normal");
  const [reloadKey, setReloadKey] = useState(0);
  const [replyMessage, setReplyMessage] = useState("");
  const [replyStatus, setReplyStatus] = useState<SupportTicketStatus>("waiting_customer");
  const [selectedTicketId, setSelectedTicketId] = useState<UUID | null>(null);
  const [statusDraft, setStatusDraft] = useState<SupportTicketStatus>("in_progress");
  const [ticket, setTicket] = useState<SupportTicketRead | null>(null);
  const [tickets, setTickets] = useState<SupportTicketSummary[]>([]);

  useEffect(() => {
    const controller = new AbortController();

    setIsListLoading(true);
    setListError(null);
    adminSupportApi
      .listTickets(
        {
          assigned_admin_id: filters.assignedAdminId.trim() || undefined,
          human_handoff_requested: parseBoolFilter(filters.handoff),
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
          priority: filters.priority || undefined,
          search: filters.search.trim() || undefined,
          status: filters.status || undefined,
        },
        { signal: controller.signal },
      )
      .then((payload) => {
        if (controller.signal.aborted) {
          return;
        }

        setTickets(payload.items);
        setSelectedTicketId((current) => (payload.items.some((item) => item.id === current) ? current : payload.items[0]?.id ?? null));
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setListError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsListLoading(false);
        }
      });

    return () => controller.abort();
  }, [filters, page, reloadKey]);

  useEffect(() => {
    if (!selectedTicketId) {
      setTicket(null);
      return undefined;
    }

    const controller = new AbortController();
    setIsDetailLoading(true);
    setDetailError(null);

    adminSupportApi
      .getTicket(selectedTicketId, { signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          replaceTicket(payload);
          setTicket(payload);
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setDetailError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [detailReloadKey, selectedTicketId]);

  useEffect(() => {
    if (!ticket) {
      return;
    }

    const allowedStatuses = SUPPORT_TRANSITIONS[ticket.status];
    setStatusDraft(allowedStatuses[0] ?? ticket.status);
    setReplyStatus(allowedStatuses.includes("waiting_customer") ? "waiting_customer" : allowedStatuses[0] ?? ticket.status);
    setPriorityDraft(ticket.priority);
    setAssignedAdminId(ticket.assigned_admin_id ?? "");
    setReplyMessage("");
  }, [ticket?.id, ticket?.status, ticket?.priority, ticket?.assigned_admin_id]);

  const summary = useMemo(
    () => ({
      active: tickets.filter((item) => ["in_progress", "open", "waiting_customer"].includes(item.status)).length,
      handoff: tickets.filter((item) => item.human_handoff_requested).length,
      loaded: tickets.length,
      urgent: tickets.filter((item) => ["high", "urgent"].includes(item.priority)).length,
    }),
    [tickets],
  );

  const allowedStatuses = ticket ? SUPPORT_TRANSITIONS[ticket.status] : [];
  const statusOptions = allowedStatuses.map((status) => ({
    label: getStatusLabel(status),
    value: status,
  }));
  const updateStatusOptions = statusOptions.length ? statusOptions : [{ label: getStatusLabel(ticket?.status ?? "open"), value: ticket?.status ?? "open" }];

  const canGoNext = tickets.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

  function replaceTicket(updatedTicket: SupportTicketRead) {
    setTickets((current) =>
      current.some((item) => item.id === updatedTicket.id)
        ? current.map((item) => (item.id === updatedTicket.id ? updatedTicket : item))
        : [updatedTicket, ...current],
    );
  }

  const refreshTickets = () => setReloadKey((current) => current + 1);
  const refreshSelectedTicket = () => setDetailReloadKey((current) => current + 1);

  const handleFilterSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(0);
    setFilters(draftFilters);
  };

  const handleFilterReset = () => {
    setDraftFilters(initialFilters);
    setFilters(initialFilters);
    setPage(0);
  };

  const handleTicketSelect = (ticketId: UUID) => {
    setSelectedTicketId(ticketId);
    setDetailError(null);
    setDetailReloadKey((current) => current + 1);
  };

  const handleUpdateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!ticket) {
      return;
    }

    setAction("update");
    setDetailError(null);

    try {
      const updatedTicket = await adminSupportApi.updateTicket(ticket.id, {
        assigned_admin_id: assignedAdminId.trim() || null,
        priority: priorityDraft,
        status: allowedStatuses.includes(statusDraft) ? statusDraft : null,
      });
      setTicket(updatedTicket);
      replaceTicket(updatedTicket);
      showToast({
        description: `${getStatusLabel(updatedTicket.status)} / ${updatedTicket.priority}`,
        title: "Support ticket updated",
        variant: "success",
      });
    } catch (caughtError) {
      setDetailError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const handleReplySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!ticket) {
      return;
    }

    setAction("reply");
    setDetailError(null);

    try {
      const updatedTicket = await adminSupportApi.reply(ticket.id, {
        message: replyMessage.trim(),
        status: allowedStatuses.includes(replyStatus) ? replyStatus : null,
      });
      setTicket(updatedTicket);
      replaceTicket(updatedTicket);
      showToast({
        description: updatedTicket.contact_email || updatedTicket.subject,
        title: "Reply sent",
        variant: "success",
      });
      setReplyMessage("");
    } catch (caughtError) {
      setDetailError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  return (
    <section className="admin-support" aria-label="Support tickets">
      <section className="admin-support-summary" aria-label="Support summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.loaded}</strong>
        </article>
        <article className="surface-card">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </article>
        <article className="surface-card">
          <span>Handoff</span>
          <strong>{summary.handoff}</strong>
        </article>
        <article className="surface-card">
          <span>High priority</span>
          <strong>{summary.urgent}</strong>
        </article>
      </section>

      <form className="admin-toolbar admin-support-toolbar" onSubmit={handleFilterSubmit}>
        <TextField
          label="Search"
          onChange={(event) => setDraftFilters((current) => ({ ...current, search: event.target.value }))}
          placeholder="Subject, email, preview"
          value={draftFilters.search}
        />
        <SelectField
          label="Status"
          onChange={(event) => setDraftFilters((current) => ({ ...current, status: event.target.value as SupportTicketStatus | "" }))}
          options={[{ label: "Any status", value: "" }, ...SUPPORT_STATUS_OPTIONS]}
          value={draftFilters.status}
        />
        <SelectField
          label="Priority"
          onChange={(event) => setDraftFilters((current) => ({ ...current, priority: event.target.value as SupportTicketPriority | "" }))}
          options={[{ label: "Any priority", value: "" }, ...SUPPORT_PRIORITY_OPTIONS]}
          value={draftFilters.priority}
        />
        <label className="ds-field">
          <span className="ds-field__label">Handoff</span>
          <select
            className="ds-input ds-select"
            onChange={(event) => setDraftFilters((current) => ({ ...current, handoff: event.target.value as BoolFilter }))}
            value={draftFilters.handoff}
          >
            <option value="all">Any handoff</option>
            <option value="true">Requested</option>
            <option value="false">Not requested</option>
          </select>
        </label>
        <TextField
          label="Assigned admin"
          onChange={(event) => setDraftFilters((current) => ({ ...current, assignedAdminId: event.target.value }))}
          placeholder="UUID"
          value={draftFilters.assignedAdminId}
        />
        <div className="admin-toolbar-actions">
          <Button type="submit">Apply</Button>
          <Button onClick={handleFilterReset} type="button" variant="secondary">
            Reset
          </Button>
          <Button onClick={refreshTickets} type="button" variant="secondary">
            Refresh
          </Button>
        </div>
      </form>

      {listError ? (
        <ErrorState
          action={
            <Button onClick={refreshTickets} variant="secondary">
              Retry
            </Button>
          }
          description={listError}
          title="Unable to load support tickets"
        />
      ) : null}

      <div className="admin-support-layout">
        <aside className="admin-support-list" aria-label="Support ticket list">
          {isListLoading ? (
            <LoadingState description="Loading support tickets." title="Loading tickets" />
          ) : tickets.length ? (
            <>
              <div className="admin-support-list__items">
                {tickets.map((item) => (
                  <button
                    className={item.id === selectedTicketId ? "admin-support-card is-active" : "admin-support-card"}
                    key={item.id}
                    onClick={() => handleTicketSelect(item.id)}
                    type="button"
                  >
                    <strong>{item.subject}</strong>
                    <span>{item.contact_email || item.id}</span>
                    <small>{item.last_message_preview || "No messages yet"}</small>
                    <span className="admin-support-card__badges">
                      <SupportBadge label={item.status} />
                      <SupportBadge label={item.priority} tone="priority" />
                      {item.human_handoff_requested ? <SupportBadge label="handoff" tone="warning" /> : null}
                    </span>
                  </button>
                ))}
              </div>
              <div className="admin-users-pagination">
                <Button disabled={!canGoPrevious || isListLoading} onClick={() => setPage((current) => Math.max(0, current - 1))} size="sm" variant="secondary">
                  Previous
                </Button>
                <span>Page {page + 1}</span>
                <Button disabled={!canGoNext || isListLoading} onClick={() => setPage((current) => current + 1)} size="sm" variant="secondary">
                  Next
                </Button>
              </div>
            </>
          ) : (
            <EmptyState description="No support tickets match the current filters." title="No support tickets" />
          )}
        </aside>

        <section className="admin-support-detail" aria-label="Support ticket details">
          {isDetailLoading ? (
            <LoadingState description="Loading selected ticket." title="Loading ticket" />
          ) : detailError ? (
            <ErrorState
              action={
                <Button onClick={refreshSelectedTicket} variant="secondary">
                  Retry
                </Button>
              }
              description={detailError}
              title="Support action failed"
            />
          ) : ticket ? (
            <div className="admin-support-detail-stack">
              <section className="admin-support-hero">
                <div>
                  <p>{ticket.id}</p>
                  <h2>{ticket.subject}</h2>
                  <span>{ticket.contact_email || "No contact email"}</span>
                </div>
                <div className="admin-support-card__badges">
                  <SupportBadge label={ticket.status} />
                  <SupportBadge label={ticket.priority} tone="priority" />
                </div>
              </section>

              <section className="admin-support-actions-grid">
                <form className="admin-order-panel" onSubmit={handleUpdateSubmit}>
                  <h3>Ticket update</h3>
                  <SelectField
                    disabled={action !== null}
                    label="Status"
                    onChange={(event) => setStatusDraft(event.target.value as SupportTicketStatus)}
                    options={updateStatusOptions}
                    value={statusDraft}
                  />
                  <SelectField
                    disabled={action !== null}
                    label="Priority"
                    onChange={(event) => setPriorityDraft(event.target.value as SupportTicketPriority)}
                    options={SUPPORT_PRIORITY_OPTIONS}
                    value={priorityDraft}
                  />
                  <TextField
                    disabled={action !== null}
                    label="Assigned admin"
                    onChange={(event) => setAssignedAdminId(event.target.value)}
                    placeholder="UUID or empty"
                    value={assignedAdminId}
                  />
                  <Button disabled={action !== null} isLoading={action === "update"} type="submit">
                    Update ticket
                  </Button>
                </form>

                <form className="admin-order-panel" onSubmit={handleReplySubmit}>
                  <h3>Admin reply</h3>
                  <SelectField
                    disabled={action !== null}
                    label="Status after reply"
                    onChange={(event) => setReplyStatus(event.target.value as SupportTicketStatus)}
                    options={updateStatusOptions}
                    value={replyStatus}
                  />
                  <label className="ds-field" htmlFor="admin-support-reply">
                    <span className="ds-field__label">Message</span>
                    <textarea
                      className="ds-input admin-textarea"
                      disabled={action !== null}
                      id="admin-support-reply"
                      maxLength={4000}
                      minLength={1}
                      onChange={(event) => setReplyMessage(event.target.value)}
                      required
                      value={replyMessage}
                    />
                  </label>
                  <Button disabled={action !== null || !replyMessage.trim()} isLoading={action === "reply"} type="submit">
                    Send reply
                  </Button>
                </form>
              </section>

              <section className="admin-order-panel">
                <h3>Ticket details</h3>
                <div className="admin-order-info-grid">
                  <InfoItem label="Created" value={formatDate(ticket.created_at)} />
                  <InfoItem label="Updated" value={formatDate(ticket.updated_at)} />
                  <InfoItem label="Customer last message" value={formatDate(ticket.last_customer_message_at)} />
                  <InfoItem label="Admin last reply" value={formatDate(ticket.last_admin_reply_at)} />
                  <InfoItem label="Human handoff" value={ticket.human_handoff_requested ? "requested" : "not requested"} />
                  <InfoItem label="AI last used" value={ticket.ai_last_used ? "yes" : "no"} />
                  <InfoItem label="Assigned admin" value={ticket.assigned_admin_id || "unassigned"} wide />
                </div>
              </section>

              <section className="admin-order-panel">
                <h3>Conversation</h3>
                <SupportConversation messages={ticket.messages} />
              </section>
            </div>
          ) : (
            <EmptyState description="Select a support ticket from the list." title="No ticket selected" />
          )}
        </section>
      </div>
    </section>
  );
}

function SupportConversation({ messages }: { messages: SupportMessageRead[] }) {
  if (!messages.length) {
    return <EmptyState description="This ticket has no messages yet." title="No messages" />;
  }

  return (
    <div className="admin-support-thread">
      {messages.map((message) => (
        <article className={message.author_type === "customer" ? "admin-support-message is-customer" : "admin-support-message"} key={message.id}>
          <div>
            <strong>{message.author_name || getStatusLabel(message.author_type)}</strong>
            <span>{formatDate(message.created_at)}</span>
          </div>
          <p>{message.body}</p>
        </article>
      ))}
    </div>
  );
}

function SupportBadge({ label, tone = "default" }: { label: string; tone?: "default" | "priority" | "warning" }) {
  return (
    <span className={tone === "warning" ? "admin-badge is-warning" : tone === "priority" ? "admin-badge" : "admin-badge is-success"}>
      {getStatusLabel(label)}
    </span>
  );
}

function InfoItem({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <article className={wide ? "admin-order-info-item is-wide" : "admin-order-info-item"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

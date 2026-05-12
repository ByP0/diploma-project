import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { supportApi } from "@features/support/api/supportApi";
import { useAuth } from "@features/auth/model/useAuth";
import { isApiError } from "@shared/api";
import type { ChatResponse, SupportMessageRead, SupportTicketRead, SupportTicketSummary, UUID } from "@shared/api";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, TextField, useToast } from "@shared/ui";
import "./SupportPage.css";

const PAGE_SIZE = 12;

type LocalChatMessage = {
  author: "ai" | "customer";
  body: string;
  createdAt: string;
  id: string;
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

function createLocalMessage(author: LocalChatMessage["author"], body: string): LocalChatMessage {
  return {
    author,
    body,
    createdAt: new Date().toISOString(),
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  };
}

function getStatusLabel(value: string) {
  return value.replace(/_/g, " ");
}

export function SupportPage() {
  const { isAuthenticated, user } = useAuth();
  const { showToast } = useToast();
  const [contactEmail, setContactEmail] = useState("");
  const [currentTicketId, setCurrentTicketId] = useState<UUID | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isTicketsLoading, setIsTicketsLoading] = useState(false);
  const [localMessages, setLocalMessages] = useState<LocalChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [page, setPage] = useState(0);
  const [requestHuman, setRequestHuman] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicketRead | null>(null);
  const [ticketIdInput, setTicketIdInput] = useState("");
  const [tickets, setTickets] = useState<SupportTicketSummary[]>([]);

  useEffect(() => {
    if (user?.email) {
      setContactEmail(user.email);
    }
  }, [user]);

  useEffect(() => {
    if (!isAuthenticated) {
      setTickets([]);
      setSelectedTicket(null);
      return undefined;
    }

    const controller = new AbortController();
    setIsTicketsLoading(true);
    setError(null);

    supportApi
      .listMyTickets({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        signal: controller.signal,
      })
      .then((payload) => {
        if (!controller.signal.aborted) {
          setTickets(payload.items);
          setCurrentTicketId((current) =>
            payload.items.some((ticket) => ticket.id === current) ? current : payload.items[0]?.id ?? current,
          );
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsTicketsLoading(false);
        }
      });

    return () => controller.abort();
  }, [isAuthenticated, page]);

  useEffect(() => {
    if (!isAuthenticated || !currentTicketId) {
      return undefined;
    }

    const controller = new AbortController();
    setIsDetailLoading(true);
    setError(null);

    supportApi
      .getTicket(currentTicketId, { signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          setSelectedTicket(payload);
          setTicketIdInput(payload.id);
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [currentTicketId, isAuthenticated]);

  const summary = useMemo(
    () => ({
      handoff: tickets.filter((ticket) => ticket.human_handoff_requested).length,
      open: tickets.filter((ticket) => ["in_progress", "open", "waiting_customer"].includes(ticket.status)).length,
      total: tickets.length,
    }),
    [tickets],
  );

  const transcriptMessages = selectedTicket?.messages ?? [];
  const canGoNext = tickets.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

  const reloadTicket = async (ticketId: UUID) => {
    if (!isAuthenticated) {
      return null;
    }

    const ticket = await supportApi.getTicket(ticketId);
    setSelectedTicket(ticket);
    setCurrentTicketId(ticket.id);
    setTicketIdInput(ticket.id);
    setTickets((current) => (current.some((item) => item.id === ticket.id) ? current : [ticket, ...current]));
    return ticket;
  };

  const reloadTickets = async () => {
    if (!isAuthenticated) {
      return;
    }

    const payload = await supportApi.listMyTickets({ limit: PAGE_SIZE, offset: page * PAGE_SIZE });
    setTickets(payload.items);
  };

  const handleTicketSelect = (ticket: SupportTicketSummary) => {
    setCurrentTicketId(ticket.id);
    setTicketIdInput(ticket.id);
    setError(null);
  };

  const handleContinueById = async () => {
    const ticketId = ticketIdInput.trim();
    if (!ticketId) {
      setError("Enter a ticket_id to continue an existing conversation.");
      return;
    }

    setCurrentTicketId(ticketId);
    if (isAuthenticated) {
      setIsDetailLoading(true);
      try {
        await reloadTicket(ticketId);
      } catch (caughtError) {
        setError(getErrorMessage(caughtError));
      } finally {
        setIsDetailLoading(false);
      }
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedMessage = message.trim();
    const normalizedTicketId = ticketIdInput.trim();
    const normalizedEmail = contactEmail.trim();

    if (!normalizedMessage) {
      setError("Message must not be empty.");
      return;
    }

    if (!isAuthenticated && normalizedTicketId && !normalizedEmail) {
      setError("Guest continuation by ticket_id requires the same contact email.");
      return;
    }

    setIsSending(true);
    setError(null);
    setLocalMessages((current) => [...current, createLocalMessage("customer", normalizedMessage)]);

    try {
      const response = await supportApi.sendChatMessage({
        contact_email: isAuthenticated ? null : normalizedEmail || null,
        message: normalizedMessage,
        request_human: requestHuman,
        ticket_id: normalizedTicketId || currentTicketId,
      });

      setCurrentTicketId(response.ticket_id);
      setTicketIdInput(response.ticket_id);
      setMessage("");
      setRequestHuman(false);
      setLocalMessages((current) => [...current, createLocalMessage("ai", response.answer)]);

      if (isAuthenticated) {
        await reloadTicket(response.ticket_id);
        await reloadTickets();
      }

      showChatToast(response);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSending(false);
    }
  };

  const showChatToast = (response: ChatResponse) => {
    showToast({
      description: `Ticket ${response.ticket_id} is ${response.ticket_status}.`,
      title: response.human_handoff_requested ? "Operator requested" : "Support replied",
      variant: response.human_handoff_requested ? "warning" : "success",
    });
  };

  return (
    <div className="support-page page-stack">
      <PageHeader
        actions={
          <Button disabled={!isAuthenticated || isTicketsLoading} onClick={() => void reloadTickets()} variant="secondary">
            Refresh tickets
          </Button>
        }
        description="Ask support a question, continue a ticket by ticket_id, and review your support requests."
        eyebrow="Support"
        title="Chat and tickets"
      />

      <section className="support-summary" aria-label="Support summary">
        <article className="surface-card">
          <span>Tickets loaded</span>
          <strong>{summary.total}</strong>
        </article>
        <article className="surface-card">
          <span>Active</span>
          <strong>{summary.open}</strong>
        </article>
        <article className="surface-card">
          <span>Human handoff</span>
          <strong>{summary.handoff}</strong>
        </article>
      </section>

      {error ? (
        <ErrorState
          action={
            <Button onClick={() => setError(null)} variant="secondary">
              Dismiss
            </Button>
          }
          description={error}
          title="Support request failed"
        />
      ) : null}

      <div className="support-layout">
        <section className="support-chat" aria-label="Support chat">
          <div className="support-panel">
            <div className="support-panel__header">
              <div>
                <h2>Chat</h2>
                <p>{currentTicketId ? `Continuing ticket ${currentTicketId}` : "New support conversation"}</p>
              </div>
              {currentTicketId ? <StatusPill value={selectedTicket?.status ?? "open"} /> : null}
            </div>

            <form className="support-ticket-controls" onSubmit={(event) => event.preventDefault()}>
              <TextField
                label="ticket_id"
                onChange={(event) => setTicketIdInput(event.target.value)}
                placeholder="Paste existing ticket ID"
                value={ticketIdInput}
              />
              {!isAuthenticated ? (
                <TextField
                  autoComplete="email"
                  label="Contact email"
                  onChange={(event) => setContactEmail(event.target.value)}
                  placeholder="guest@example.com"
                  type="email"
                  value={contactEmail}
                />
              ) : null}
              <Button disabled={isDetailLoading || !ticketIdInput.trim()} onClick={() => void handleContinueById()} type="button" variant="secondary">
                Continue by ID
              </Button>
            </form>

            <MessageList localMessages={localMessages} ticketMessages={transcriptMessages} />

            <form className="support-message-form" onSubmit={handleSubmit}>
              <label className="support-textarea-field">
                <span>Message</span>
                <textarea
                  maxLength={2000}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Ask about catalog, orders, delivery, payment, or request an operator."
                  required
                  value={message}
                />
              </label>
              <label className="support-checkbox">
                <input checked={requestHuman} onChange={(event) => setRequestHuman(event.target.checked)} type="checkbox" />
                <span>Request human operator</span>
              </label>
              <Button disabled={isSending} isLoading={isSending} type="submit">
                Send message
              </Button>
            </form>
          </div>
        </section>

        <aside className="support-tickets" aria-label="My support tickets">
          <div className="support-panel">
            <div className="support-panel__header">
              <div>
                <h2>My tickets</h2>
                <p>{isAuthenticated ? "Tickets from your account" : "Sign in to see your ticket list"}</p>
              </div>
            </div>

            {!isAuthenticated ? (
              <EmptyState description="Guest chat still works. Use ticket_id and contact email to continue later." title="Ticket list needs sign in" />
            ) : isTicketsLoading ? (
              <LoadingState description="Loading your support tickets." title="Loading tickets" />
            ) : tickets.length ? (
              <>
                <div className="support-ticket-list">
                  {tickets.map((ticket) => (
                    <button
                      className={ticket.id === currentTicketId ? "support-ticket-card is-active" : "support-ticket-card"}
                      key={ticket.id}
                      onClick={() => handleTicketSelect(ticket)}
                      type="button"
                    >
                      <div>
                        <strong>{ticket.subject}</strong>
                        <span>{ticket.last_message_preview || "No messages yet"}</span>
                      </div>
                      <div className="support-ticket-card__meta">
                        <StatusPill value={ticket.status} />
                        <small>{formatDate(ticket.updated_at)}</small>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="support-pagination">
                  <Button disabled={!canGoPrevious || isTicketsLoading} onClick={() => setPage((current) => Math.max(0, current - 1))} size="sm" variant="secondary">
                    Previous
                  </Button>
                  <span>Page {page + 1}</span>
                  <Button disabled={!canGoNext || isTicketsLoading} onClick={() => setPage((current) => current + 1)} size="sm" variant="secondary">
                    Next
                  </Button>
                </div>
              </>
            ) : (
              <EmptyState description="Send a chat message and the ticket will appear here." title="No tickets yet" />
            )}
          </div>

          <TicketDetails isLoading={isDetailLoading} ticket={selectedTicket} />
        </aside>
      </div>
    </div>
  );
}

type MessageListProps = {
  localMessages: LocalChatMessage[];
  ticketMessages: SupportMessageRead[];
};

function MessageList({ localMessages, ticketMessages }: MessageListProps) {
  const messages: Array<SupportMessageRead | LocalChatMessage> = ticketMessages.length ? ticketMessages : localMessages;

  if (!messages.length) {
    return (
      <div className="support-empty-thread">
        <strong>No messages yet</strong>
        <span>Start a chat or select an existing ticket.</span>
      </div>
    );
  }

  return (
    <div className="support-thread" aria-label="Conversation">
      {messages.map((message) => {
        const author = "author_type" in message ? message.author_type : message.author;
        const createdAt = "created_at" in message ? message.created_at : message.createdAt;
        const body = message.body;
        const authorName = "author_name" in message ? message.author_name : author;

        return (
          <article className={author === "customer" ? "support-message is-customer" : "support-message"} key={message.id}>
            <div>
              <strong>{authorName || getStatusLabel(author)}</strong>
              <span>{formatDate(createdAt)}</span>
            </div>
            <p>{body}</p>
          </article>
        );
      })}
    </div>
  );
}

type TicketDetailsProps = {
  isLoading: boolean;
  ticket: SupportTicketRead | null;
};

function TicketDetails({ isLoading, ticket }: TicketDetailsProps) {
  if (isLoading) {
    return (
      <div className="support-panel">
        <LoadingState description="Loading support ticket details." title="Loading ticket" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="support-panel">
        <EmptyState description="Select a ticket to inspect status and messages." title="No ticket selected" />
      </div>
    );
  }

  return (
    <div className="support-panel support-ticket-details">
      <div className="support-panel__header">
        <div>
          <h2>Ticket details</h2>
          <p>{ticket.id}</p>
        </div>
        <StatusPill value={ticket.status} />
      </div>
      <div className="support-detail-grid">
        <DetailItem label="Priority" value={ticket.priority} />
        <DetailItem label="Created" value={formatDate(ticket.created_at)} />
        <DetailItem label="Updated" value={formatDate(ticket.updated_at)} />
        <DetailItem label="Contact" value={ticket.contact_email || "account email"} />
        <DetailItem label="Human handoff" value={ticket.human_handoff_requested ? "requested" : "not requested"} />
        <DetailItem label="AI last used" value={ticket.ai_last_used ? "yes" : "no"} />
      </div>
    </div>
  );
}

type DetailItemProps = {
  label: string;
  value: string;
};

function DetailItem({ label, value }: DetailItemProps) {
  return (
    <article className="support-detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function StatusPill({ value }: { value: string }) {
  return <span className="support-status-pill">{getStatusLabel(value)}</span>;
}

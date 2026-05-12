import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminNotificationsApi } from "@features/adminNotifications/api/adminNotificationsApi";
import { isApiError } from "@shared/api";
import type { NotificationMessageRead } from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, TextField, useToast } from "@shared/ui";

const PAGE_SIZE = 50;

type NotificationFiltersForm = {
  channel: string;
  recipient: string;
  status: string;
  templateName: string;
};

const initialFilters: NotificationFiltersForm = {
  channel: "",
  recipient: "",
  status: "",
  templateName: "",
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Notification request failed.";
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

export function AdminNotificationsPanel() {
  const { showToast } = useToast();
  const [draftFilters, setDraftFilters] = useState<NotificationFiltersForm>(initialFilters);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<NotificationFiltersForm>(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<NotificationMessageRead[]>([]);
  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);
    setError(null);
    adminNotificationsApi
      .listMessages(
        {
          channel: filters.channel.trim() || undefined,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
          recipient: filters.recipient.trim() || undefined,
          status: filters.status.trim() || undefined,
          template_name: filters.templateName.trim() || undefined,
        },
        { signal: controller.signal },
      )
      .then((payload) => {
        if (!controller.signal.aborted) {
          setMessages(payload);
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [filters, page, reloadKey]);

  const summary = useMemo(
    () => ({
      failed: messages.filter((message) => message.status === "failed").length,
      loaded: messages.length,
      queued: messages.filter((message) => ["queued", "retrying"].includes(message.status)).length,
      sent: messages.filter((message) => message.status === "sent").length,
    }),
    [messages],
  );

  const canGoNext = messages.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

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

  const refreshMessages = () => setReloadKey((current) => current + 1);

  const handleProcessQueue = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await adminNotificationsApi.processQueue();
      showToast({
        description: response.detail,
        title: "Notification queue processed",
        variant: "success",
      });
      refreshMessages();
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Queue processing failed",
        variant: "error",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <section className="admin-notifications" aria-label="Notification messages">
      <section className="admin-notifications-summary" aria-label="Notification summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.loaded}</strong>
        </article>
        <article className="surface-card">
          <span>Queued</span>
          <strong>{summary.queued}</strong>
        </article>
        <article className="surface-card">
          <span>Sent</span>
          <strong>{summary.sent}</strong>
        </article>
        <article className="surface-card">
          <span>Failed</span>
          <strong>{summary.failed}</strong>
        </article>
      </section>

      <form className="admin-toolbar admin-notifications-toolbar" onSubmit={handleFilterSubmit}>
        <label className="ds-field">
          <span className="ds-field__label">Status</span>
          <select
            className="ds-input ds-select"
            onChange={(event) => setDraftFilters((current) => ({ ...current, status: event.target.value }))}
            value={draftFilters.status}
          >
            <option value="">Any status</option>
            <option value="queued">Queued</option>
            <option value="retrying">Retrying</option>
            <option value="sent">Sent</option>
            <option value="failed">Failed</option>
          </select>
        </label>
        <TextField
          label="Channel"
          maxLength={32}
          onChange={(event) => setDraftFilters((current) => ({ ...current, channel: event.target.value }))}
          placeholder="email"
          value={draftFilters.channel}
        />
        <TextField
          label="Template"
          maxLength={64}
          onChange={(event) => setDraftFilters((current) => ({ ...current, templateName: event.target.value }))}
          placeholder="support_reply"
          value={draftFilters.templateName}
        />
        <TextField
          label="Recipient"
          maxLength={255}
          onChange={(event) => setDraftFilters((current) => ({ ...current, recipient: event.target.value }))}
          placeholder="customer@example.com"
          value={draftFilters.recipient}
        />
        <div className="admin-toolbar-actions">
          <Button type="submit">Apply</Button>
          <Button onClick={handleFilterReset} type="button" variant="secondary">
            Reset
          </Button>
          <Button onClick={refreshMessages} type="button" variant="secondary">
            Refresh
          </Button>
          <Button isLoading={isProcessing} onClick={() => void handleProcessQueue()} type="button">
            Process queue
          </Button>
        </div>
      </form>

      {error ? (
        <ErrorState
          action={
            <Button onClick={refreshMessages} variant="secondary">
              Retry
            </Button>
          }
          description={error}
          title="Unable to load notifications"
        />
      ) : null}

      {isLoading ? (
        <LoadingState description="Loading notification messages." title="Loading notifications" />
      ) : (
        <>
          <DataTable
            columns={[
              { key: "created", title: "Created", render: (message) => formatDate(message.created_at) },
              { key: "status", title: "Status", render: (message) => <NotificationStatusBadge status={message.status} /> },
              { key: "channel", title: "Channel", render: (message) => message.channel },
              { key: "template", title: "Template", render: (message) => message.template_name },
              { key: "recipient", title: "Recipient", render: (message) => message.recipient },
              { key: "subject", title: "Subject", render: (message) => message.subject },
              { key: "attempts", title: "Attempts", render: (message) => `${message.attempts}/${message.max_attempts}` },
              { key: "next", title: "Next retry", render: (message) => formatDate(message.next_retry_at) },
              { key: "error", title: "Last error", render: (message) => message.last_error || "none" },
            ]}
            empty={<EmptyState description="No notification messages match the current filters." title="No notifications" />}
            getRowKey={(message) => message.id}
            rows={messages}
          />

          <div className="admin-users-pagination">
            <Button disabled={!canGoPrevious || isLoading} onClick={() => setPage((current) => Math.max(0, current - 1))} size="sm" variant="secondary">
              Previous
            </Button>
            <span>Page {page + 1}</span>
            <Button disabled={!canGoNext || isLoading} onClick={() => setPage((current) => current + 1)} size="sm" variant="secondary">
              Next
            </Button>
          </div>
        </>
      )}
    </section>
  );
}

function NotificationStatusBadge({ status }: { status: string }) {
  if (status === "sent") {
    return <span className="admin-badge is-success">Sent</span>;
  }

  if (status === "failed") {
    return <span className="admin-badge is-warning">Failed</span>;
  }

  return <span className="admin-badge">{status}</span>;
}

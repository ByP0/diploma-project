import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminUsersApi } from "@features/adminUsers/api/adminUsersApi";
import { isApiError } from "@shared/api";
import type { UserLoginAuditRead } from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, TextField } from "@shared/ui";

const PAGE_SIZE = 100;

type AuditSuccessFilter = "all" | "false" | "true";

type AuditFiltersForm = {
  createdFrom: string;
  createdTo: string;
  email: string;
  eventType: string;
  ipAddress: string;
  success: AuditSuccessFilter;
  userId: string;
};

const initialFilters: AuditFiltersForm = {
  createdFrom: "",
  createdTo: "",
  email: "",
  eventType: "",
  ipAddress: "",
  success: "all",
  userId: "",
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Login audit request failed.";
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

function parseSuccessFilter(value: AuditSuccessFilter) {
  if (value === "all") {
    return undefined;
  }

  return value === "true";
}

function normalizeDateFilter(value: string) {
  if (!value) {
    return undefined;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toISOString();
}

export function AdminLoginAuditPanel() {
  const [auditRows, setAuditRows] = useState<UserLoginAuditRead[]>([]);
  const [draftFilters, setDraftFilters] = useState<AuditFiltersForm>(initialFilters);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AuditFiltersForm>(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);
    setError(null);
    adminUsersApi
      .listLoginAudit(
        {
          created_from: normalizeDateFilter(filters.createdFrom),
          created_to: normalizeDateFilter(filters.createdTo),
          email: filters.email.trim() || undefined,
          event_type: filters.eventType.trim() || undefined,
          ip_address: filters.ipAddress.trim() || undefined,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
          success: parseSuccessFilter(filters.success),
          user_id: filters.userId.trim() || undefined,
        },
        { signal: controller.signal },
      )
      .then((payload) => {
        if (!controller.signal.aborted) {
          setAuditRows(payload);
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
      failed: auditRows.filter((row) => !row.success).length,
      loaded: auditRows.length,
      success: auditRows.filter((row) => row.success).length,
      uniqueEmails: new Set(auditRows.map((row) => row.email)).size,
    }),
    [auditRows],
  );

  const canGoNext = auditRows.length === PAGE_SIZE;
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

  const refreshAudit = () => setReloadKey((current) => current + 1);

  return (
    <section className="admin-audit" aria-label="Login audit">
      <section className="admin-audit-summary" aria-label="Login audit summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.loaded}</strong>
        </article>
        <article className="surface-card">
          <span>Successful</span>
          <strong>{summary.success}</strong>
        </article>
        <article className="surface-card">
          <span>Failed</span>
          <strong>{summary.failed}</strong>
        </article>
        <article className="surface-card">
          <span>Emails</span>
          <strong>{summary.uniqueEmails}</strong>
        </article>
      </section>

      <form className="admin-toolbar admin-audit-toolbar" onSubmit={handleFilterSubmit}>
        <TextField
          label="Email"
          onChange={(event) => setDraftFilters((current) => ({ ...current, email: event.target.value }))}
          placeholder="buyer@example.com"
          value={draftFilters.email}
        />
        <TextField
          label="User ID"
          onChange={(event) => setDraftFilters((current) => ({ ...current, userId: event.target.value }))}
          placeholder="UUID"
          value={draftFilters.userId}
        />
        <label className="ds-field">
          <span className="ds-field__label">Success</span>
          <select
            className="ds-input ds-select"
            onChange={(event) => setDraftFilters((current) => ({ ...current, success: event.target.value as AuditSuccessFilter }))}
            value={draftFilters.success}
          >
            <option value="all">Any result</option>
            <option value="true">Success</option>
            <option value="false">Failure</option>
          </select>
        </label>
        <TextField
          label="Event"
          maxLength={32}
          onChange={(event) => setDraftFilters((current) => ({ ...current, eventType: event.target.value }))}
          placeholder="login"
          value={draftFilters.eventType}
        />
        <TextField
          label="IP address"
          maxLength={64}
          onChange={(event) => setDraftFilters((current) => ({ ...current, ipAddress: event.target.value }))}
          placeholder="127.0.0.1"
          value={draftFilters.ipAddress}
        />
        <TextField
          label="From"
          onChange={(event) => setDraftFilters((current) => ({ ...current, createdFrom: event.target.value }))}
          type="datetime-local"
          value={draftFilters.createdFrom}
        />
        <TextField
          label="To"
          onChange={(event) => setDraftFilters((current) => ({ ...current, createdTo: event.target.value }))}
          type="datetime-local"
          value={draftFilters.createdTo}
        />
        <div className="admin-toolbar-actions">
          <Button type="submit">Apply</Button>
          <Button onClick={handleFilterReset} type="button" variant="secondary">
            Reset
          </Button>
          <Button onClick={refreshAudit} type="button" variant="secondary">
            Refresh
          </Button>
        </div>
      </form>

      {error ? (
        <ErrorState
          action={
            <Button onClick={refreshAudit} variant="secondary">
              Retry
            </Button>
          }
          description={error}
          title="Unable to load login audit"
        />
      ) : null}

      {isLoading ? (
        <LoadingState description="Loading login audit events." title="Loading login audit" />
      ) : (
        <>
          <DataTable
            columns={[
              { key: "created", title: "Created", render: (row) => formatDate(row.created_at) },
              {
                key: "result",
                title: "Result",
                render: (row) => (
                  <span className={row.success ? "admin-badge is-success" : "admin-badge is-warning"}>
                    {row.success ? "Success" : "Failure"}
                  </span>
                ),
              },
              { key: "email", title: "Email", render: (row) => row.email },
              { key: "event", title: "Event", render: (row) => row.event_type },
              { key: "reason", title: "Failure reason", render: (row) => row.failure_reason || "none" },
              { key: "ip", title: "IP", render: (row) => row.ip_address || "unknown" },
              { key: "user", title: "User ID", render: (row) => row.user_id || "not linked" },
              { key: "agent", title: "User agent", render: (row) => <span className="admin-audit-agent">{row.user_agent || "unknown"}</span> },
            ]}
            empty={<EmptyState description="No login audit events match the current filters." title="No audit events" />}
            getRowKey={(row) => row.id}
            rows={auditRows}
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

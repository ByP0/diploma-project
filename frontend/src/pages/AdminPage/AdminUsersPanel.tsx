import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminUsersApi } from "@features/adminUsers/api/adminUsersApi";
import { isApiError } from "@shared/api";
import type { UserAdminUpdate, UserRead, UserRole } from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, Modal, SelectField, TextField, useToast } from "@shared/ui";

const PAGE_SIZE = 50;

const ROLE_OPTIONS: Array<{ label: string; value: UserRole }> = [
  { label: "User", value: "user" },
  { label: "Admin", value: "admin" },
  { label: "Manager", value: "manager" },
  { label: "Support", value: "support" },
];

type AnyFilter = "all";
type BoolFilter = AnyFilter | "false" | "true";
type RoleFilter = AnyFilter | UserRole;

type UserFiltersForm = {
  active: BoolFilter;
  blocked: BoolFilter;
  role: RoleFilter;
  search: string;
  verified: BoolFilter;
};

type UserAccessForm = {
  blockedReason: string;
  emailVerified: boolean;
  isActive: boolean;
  isBlocked: boolean;
  role: UserRole;
};

const initialFilters: UserFiltersForm = {
  active: "all",
  blocked: "all",
  role: "all",
  search: "",
  verified: "all",
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "User request failed.";
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

function parseBoolFilter(value: BoolFilter) {
  if (value === "all") {
    return undefined;
  }

  return value === "true";
}

function toUserAccessForm(user: UserRead): UserAccessForm {
  return {
    blockedReason: user.blocked_reason ?? "",
    emailVerified: user.is_email_verified,
    isActive: user.is_active,
    isBlocked: user.is_blocked,
    role: user.role,
  };
}

export function AdminUsersPanel() {
  const { showToast } = useToast();
  const [accessForm, setAccessForm] = useState<UserAccessForm | null>(null);
  const [draftFilters, setDraftFilters] = useState<UserFiltersForm>(initialFilters);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<UserFiltersForm>(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [mutation, setMutation] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedUser, setSelectedUser] = useState<UserRead | null>(null);
  const [users, setUsers] = useState<UserRead[]>([]);

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);
    setError(null);
    adminUsersApi
      .listUsers(
        {
          email_verified: parseBoolFilter(filters.verified),
          is_active: parseBoolFilter(filters.active),
          is_blocked: parseBoolFilter(filters.blocked),
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
          role: filters.role === "all" ? undefined : filters.role,
          search: filters.search.trim() || undefined,
        },
        { signal: controller.signal },
      )
      .then((payload) => {
        if (!controller.signal.aborted) {
          setUsers(payload);
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
      active: users.filter((user) => user.is_active).length,
      admins: users.filter((user) => user.role === "admin").length,
      blocked: users.filter((user) => user.is_blocked).length,
      loaded: users.length,
      verified: users.filter((user) => user.is_email_verified).length,
    }),
    [users],
  );

  const canGoNext = users.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

  const openEditUser = (user: UserRead) => {
    setSelectedUser(user);
    setAccessForm(toUserAccessForm(user));
  };

  const closeEditUser = () => {
    setSelectedUser(null);
    setAccessForm(null);
  };

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

  const handleSaveAccess = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedUser || !accessForm) {
      return;
    }

    const payload: UserAdminUpdate = {
      blocked_reason: accessForm.isBlocked ? accessForm.blockedReason.trim() || "Blocked by staff" : null,
      email_verified: accessForm.emailVerified,
      is_active: accessForm.isActive,
      is_blocked: accessForm.isBlocked,
      role: accessForm.role,
    };

    setMutation("user-access");
    setError(null);

    try {
      const updatedUser = await adminUsersApi.updateUserAccess(selectedUser.id, payload);
      setUsers((current) => current.map((user) => (user.id === updatedUser.id ? updatedUser : user)));
      showToast({
        description: `${updatedUser.email} is now ${updatedUser.role}.`,
        title: "User access updated",
        variant: "success",
      });
      closeEditUser();
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "User update failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const refreshUsers = () => setReloadKey((current) => current + 1);

  return (
    <section className="admin-users" aria-label="User management">
      <section className="admin-users-summary" aria-label="User summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.loaded}</strong>
        </article>
        <article className="surface-card">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </article>
        <article className="surface-card">
          <span>Blocked</span>
          <strong>{summary.blocked}</strong>
        </article>
        <article className="surface-card">
          <span>Verified</span>
          <strong>{summary.verified}</strong>
        </article>
        <article className="surface-card">
          <span>Admins</span>
          <strong>{summary.admins}</strong>
        </article>
      </section>

      <form className="admin-toolbar admin-users-toolbar" onSubmit={handleFilterSubmit}>
        <TextField
          label="Search"
          onChange={(event) => setDraftFilters((current) => ({ ...current, search: event.target.value }))}
          placeholder="Email or name"
          value={draftFilters.search}
        />
        <SelectField
          label="Role"
          onChange={(event) => setDraftFilters((current) => ({ ...current, role: event.target.value as RoleFilter }))}
          options={[{ label: "All roles", value: "all" }, ...ROLE_OPTIONS]}
          value={draftFilters.role}
        />
        <SelectField
          label="Active"
          onChange={(event) => setDraftFilters((current) => ({ ...current, active: event.target.value as BoolFilter }))}
          options={[
            { label: "Any active state", value: "all" },
            { label: "Active", value: "true" },
            { label: "Inactive", value: "false" },
          ]}
          value={draftFilters.active}
        />
        <SelectField
          label="Blocked"
          onChange={(event) => setDraftFilters((current) => ({ ...current, blocked: event.target.value as BoolFilter }))}
          options={[
            { label: "Any block state", value: "all" },
            { label: "Blocked", value: "true" },
            { label: "Not blocked", value: "false" },
          ]}
          value={draftFilters.blocked}
        />
        <SelectField
          label="Email"
          onChange={(event) => setDraftFilters((current) => ({ ...current, verified: event.target.value as BoolFilter }))}
          options={[
            { label: "Any verification", value: "all" },
            { label: "Verified", value: "true" },
            { label: "Unverified", value: "false" },
          ]}
          value={draftFilters.verified}
        />
        <div className="admin-toolbar-actions">
          <Button type="submit">Apply</Button>
          <Button onClick={handleFilterReset} type="button" variant="secondary">
            Reset
          </Button>
          <Button onClick={refreshUsers} type="button" variant="secondary">
            Refresh
          </Button>
        </div>
      </form>

      {error ? (
        <ErrorState
          action={
            <Button onClick={refreshUsers} variant="secondary">
              Retry
            </Button>
          }
          description={error}
          title="Unable to load users"
        />
      ) : null}

      {isLoading ? (
        <LoadingState description="Loading users with the selected filters." title="Loading users" />
      ) : (
        <>
          <DataTable
            columns={[
              {
                key: "user",
                title: "User",
                render: (user) => (
                  <div className="admin-user-cell">
                    <div className="admin-user-avatar">
                      {user.avatar_url ? <img alt="" src={user.avatar_url} /> : <span>{user.email.slice(0, 1).toUpperCase()}</span>}
                    </div>
                    <div>
                      <strong>{user.email}</strong>
                      <span>{user.name || "No name"}</span>
                    </div>
                  </div>
                ),
              },
              { key: "role", title: "Role", render: (user) => <span className="admin-badge">{user.role}</span> },
              {
                key: "active",
                title: "Active",
                render: (user) => <BooleanBadge value={user.is_active} />,
              },
              {
                key: "blocked",
                title: "Blocked",
                render: (user) => <BooleanBadge danger value={user.is_blocked} />,
              },
              {
                key: "verified",
                title: "Verified",
                render: (user) => <BooleanBadge value={user.is_email_verified} />,
              },
              { key: "created", title: "Created", render: (user) => formatDate(user.created_at) },
              {
                align: "right",
                key: "actions",
                title: "Actions",
                render: (user) => (
                  <Button onClick={() => openEditUser(user)} size="sm" variant="secondary">
                    Edit access
                  </Button>
                ),
              },
            ]}
            empty={<EmptyState description="No users match the current filters." title="No users" />}
            getRowKey={(user) => user.id}
            rows={users}
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

      <Modal
        footer={
          <>
            <Button onClick={closeEditUser} variant="secondary">
              Cancel
            </Button>
            <Button form="user-access-form" isLoading={mutation === "user-access"} type="submit">
              Save
            </Button>
          </>
        }
        isOpen={Boolean(selectedUser && accessForm)}
        onClose={closeEditUser}
        title="Edit user access"
      >
        {selectedUser && accessForm ? (
          <form className="admin-form" id="user-access-form" onSubmit={handleSaveAccess}>
            <div className="admin-user-edit-head">
              <strong>{selectedUser.email}</strong>
              <span>{selectedUser.id}</span>
            </div>
            <SelectField
              label="Role"
              onChange={(event) => setAccessForm((current) => current && { ...current, role: event.target.value as UserRole })}
              options={ROLE_OPTIONS}
              value={accessForm.role}
            />
            <label className="admin-checkbox">
              <input
                checked={accessForm.isActive}
                onChange={(event) => setAccessForm((current) => current && { ...current, isActive: event.target.checked })}
                type="checkbox"
              />
              <span>Active</span>
            </label>
            <label className="admin-checkbox">
              <input
                checked={accessForm.isBlocked}
                onChange={(event) => setAccessForm((current) => current && { ...current, isBlocked: event.target.checked })}
                type="checkbox"
              />
              <span>Blocked</span>
            </label>
            <label className="admin-checkbox">
              <input
                checked={accessForm.emailVerified}
                onChange={(event) => setAccessForm((current) => current && { ...current, emailVerified: event.target.checked })}
                type="checkbox"
              />
              <span>Email verified</span>
            </label>
            <TextField
              disabled={!accessForm.isBlocked}
              label="Blocked reason"
              maxLength={500}
              onChange={(event) => setAccessForm((current) => current && { ...current, blockedReason: event.target.value })}
              placeholder="Blocked by staff"
              value={accessForm.blockedReason}
            />
          </form>
        ) : null}
      </Modal>
    </section>
  );
}

function BooleanBadge({ danger = false, value }: { danger?: boolean; value: boolean }) {
  if (value) {
    return <span className={danger ? "admin-badge is-warning" : "admin-badge is-success"}>Yes</span>;
  }

  return <span className="admin-badge is-muted">No</span>;
}

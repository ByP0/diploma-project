import * as React from "react";

const defaultMaxFailures = 5;
const defaultWindowMs = 5 * 60 * 1000;
const defaultLockoutMs = 15 * 60 * 1000;

interface StoredLockState {
  attempts: number;
  firstAttemptAt: number;
  lockedUntil: number | null;
}

export interface BruteForceLockOptions {
  maxFailures?: number;
  windowMs?: number;
  lockoutMs?: number;
}

export interface BruteForceLockState {
  attempts: number;
  remainingAttempts: number;
  lockedUntil: number | null;
  remainingMs: number;
  isLocked: boolean;
  registerFailure: () => void;
  reset: () => void;
}

export function useBruteForceLock(
  scope: string,
  identifier: string,
  options: BruteForceLockOptions = {},
): BruteForceLockState {
  const maxFailures = options.maxFailures ?? defaultMaxFailures;
  const windowMs = options.windowMs ?? defaultWindowMs;
  const lockoutMs = options.lockoutMs ?? defaultLockoutMs;
  const storageKey = buildStorageKey(scope, identifier);
  const [tick, setTick] = React.useState(0);
  const state = readState(storageKey, windowMs);
  const now = Date.now();
  const remainingMs = Math.max((state.lockedUntil ?? 0) - now, 0);
  const isLocked = remainingMs > 0;

  React.useEffect(() => {
    if (!isLocked) {
      return;
    }

    const timer = globalThis.setInterval(() => setTick((value) => value + 1), 1000);
    return () => globalThis.clearInterval(timer);
  }, [isLocked]);

  return {
    attempts: state.attempts,
    remainingAttempts: Math.max(maxFailures - state.attempts, 0),
    lockedUntil: state.lockedUntil,
    remainingMs,
    isLocked,
    registerFailure: () => {
      const current = readState(storageKey, windowMs);
      const nextAttempts = current.attempts + 1;
      const nextState: StoredLockState = {
        attempts: nextAttempts,
        firstAttemptAt: current.firstAttemptAt || Date.now(),
        lockedUntil: nextAttempts >= maxFailures ? Date.now() + lockoutMs : current.lockedUntil,
      };
      writeState(storageKey, nextState);
      setTick((value) => value + 1);
    },
    reset: () => {
      removeState(storageKey);
      setTick((value) => value + 1);
    },
  };
}

export function formatLockoutTime(ms: number) {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function buildStorageKey(scope: string, identifier: string) {
  return `auth-lock:${scope}:${identifier.trim().toLowerCase() || "anonymous"}`;
}

function readState(key: string, windowMs: number): StoredLockState {
  if (typeof localStorage === "undefined") {
    return createEmptyState();
  }

  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "null") as StoredLockState | null;
    if (!parsed) {
      return createEmptyState();
    }

    const now = Date.now();
    if (parsed.lockedUntil && parsed.lockedUntil > now) {
      return parsed;
    }

    if (parsed.firstAttemptAt + windowMs < now) {
      removeState(key);
      return createEmptyState();
    }

    if (parsed.lockedUntil && parsed.lockedUntil <= now) {
      removeState(key);
      return createEmptyState();
    }

    return parsed;
  } catch {
    return createEmptyState();
  }
}

function writeState(key: string, state: StoredLockState) {
  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.setItem(key, JSON.stringify(state));
}

function removeState(key: string) {
  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.removeItem(key);
}

function createEmptyState(): StoredLockState {
  return {
    attempts: 0,
    firstAttemptAt: Date.now(),
    lockedUntil: null,
  };
}

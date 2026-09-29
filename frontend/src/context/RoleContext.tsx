"use client";

import {
  createContext,
  useCallback,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";

export type Role = "student" | "parent" | "admin";

const STORAGE_KEY = "scioly.role";

export interface RoleContextValue {
  role: Role | null;
  setRole: (role: Role | null) => void;
}

export const RoleContext = createContext<RoleContextValue | undefined>(
  undefined,
);

function isRole(value: unknown): value is Role {
  return value === "student" || value === "parent" || value === "admin";
}

// A tiny external store backed by localStorage. Using useSyncExternalStore
// (rather than useState + useEffect) keeps this SSR-safe: the server/initial
// hydration render always sees `null`, and React reconciles the real value
// right after mount without the "setState in an effect" cascading-render
// pattern.
type Listener = () => void;
const listeners = new Set<Listener>();

function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): Role | null {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return isRole(stored) ? stored : null;
  } catch {
    return null;
  }
}

function getServerSnapshot(): Role | null {
  return null;
}

function writeRole(next: Role | null) {
  try {
    if (next) {
      window.localStorage.setItem(STORAGE_KEY, next);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Ignore storage failures (e.g. private browsing); listeners still fire
    // so in-memory state stays consistent for this tab.
  }
  listeners.forEach((listener) => listener());
}

export function RoleProvider({ children }: { children: ReactNode }) {
  const role = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setRole = useCallback((next: Role | null) => {
    writeRole(next);
  }, []);

  const value = useMemo(() => ({ role, setRole }), [role, setRole]);

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

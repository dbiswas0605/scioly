"use client";

import { useCallback, useSyncExternalStore } from "react";

// Same localStorage-backed external-store pattern as RoleContext — SSR-safe,
// no "setState in an effect" cascading render.
const STORAGE_KEY = "scioly.studentName";

type Listener = () => void;
const listeners = new Set<Listener>();

function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): string {
  try {
    return window.localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function getServerSnapshot(): string {
  return "";
}

function writeStudentName(next: string) {
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

export function useStudentName() {
  const studentName = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const setStudentName = useCallback((next: string) => writeStudentName(next), []);
  return { studentName, setStudentName };
}

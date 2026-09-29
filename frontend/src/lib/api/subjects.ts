import { apiFetch } from "@/lib/api/client";
import type { Subject } from "@/lib/api/types";

export function getSubjects(): Promise<Subject[]> {
  return apiFetch<Subject[]>("/api/subjects", { cache: "no-store" });
}

export function createSubject(name: string): Promise<Subject> {
  return apiFetch<Subject>("/api/subjects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

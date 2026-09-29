import { apiFetch } from "@/lib/api/client";
import type { Student } from "@/lib/api/types";

export function getStudents(): Promise<Student[]> {
  return apiFetch<Student[]>("/api/students", { cache: "no-store" });
}

export function createStudent(displayName: string): Promise<Student> {
  return apiFetch<Student>("/api/students", {
    method: "POST",
    body: JSON.stringify({ display_name: displayName }),
  });
}

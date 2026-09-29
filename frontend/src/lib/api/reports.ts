import { apiFetch } from "@/lib/api/client";
import type { StudentOverview, StudentPaperReport } from "@/lib/api/types";

export function getStudentOverviews(): Promise<StudentOverview[]> {
  return apiFetch<StudentOverview[]>("/api/reports/students", { cache: "no-store" });
}

export function getAttemptReports(): Promise<StudentPaperReport[]> {
  return apiFetch<StudentPaperReport[]>("/api/reports/attempts", { cache: "no-store" });
}

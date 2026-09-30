import { apiFetch } from "@/lib/api/client";
import type {
  AnswerInput,
  AttemptReview,
  ExamAttemptSummary,
  ExamSession,
} from "@/lib/api/types";

export function startAttempt(paperId: string, studentName: string): Promise<ExamSession> {
  return apiFetch<ExamSession>(`/api/papers/${paperId}/attempts`, {
    method: "POST",
    body: JSON.stringify({ student_name: studentName }),
  });
}

export function getAttemptSession(attemptId: string): Promise<ExamSession> {
  return apiFetch<ExamSession>(`/api/attempts/${attemptId}`, { cache: "no-store" });
}

export function submitAttempt(
  attemptId: string,
  answers: AnswerInput[],
  reason: "submitted" | "timed_out" = "submitted",
): Promise<AttemptReview> {
  return apiFetch<AttemptReview>(`/api/attempts/${attemptId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers, reason }),
  });
}

export function getAttemptReview(attemptId: string): Promise<AttemptReview> {
  return apiFetch<AttemptReview>(`/api/attempts/${attemptId}/review`, {
    cache: "no-store",
  });
}

export function getPaperAttempts(
  paperId: string,
  studentId?: string,
): Promise<ExamAttemptSummary[]> {
  const query = studentId ? `?student_id=${studentId}` : "";
  return apiFetch<ExamAttemptSummary[]>(`/api/papers/${paperId}/attempts${query}`, {
    cache: "no-store",
  });
}

export function getStudentAttempts(studentId: string): Promise<ExamAttemptSummary[]> {
  return apiFetch<ExamAttemptSummary[]>(`/api/students/${studentId}/attempts`, {
    cache: "no-store",
  });
}

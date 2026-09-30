import { apiFetch } from "@/lib/api/client";
import type { QuestionPaper } from "@/lib/api/types";

export function getPapers(): Promise<QuestionPaper[]> {
  return apiFetch<QuestionPaper[]>("/api/papers", { cache: "no-store" });
}

export function getPaper(paperId: string): Promise<QuestionPaper> {
  return apiFetch<QuestionPaper>(`/api/papers/${paperId}`, { cache: "no-store" });
}

export function uploadPaper(formData: FormData): Promise<QuestionPaper> {
  return apiFetch<QuestionPaper>("/api/papers/upload", {
    method: "POST",
    body: formData,
  });
}

export function parsePaper(paperId: string): Promise<QuestionPaper> {
  return apiFetch<QuestionPaper>(`/api/papers/${paperId}/parse`, {
    method: "POST",
  });
}

export function publishPaper(paperId: string): Promise<QuestionPaper> {
  return apiFetch<QuestionPaper>(`/api/papers/${paperId}/publish`, {
    method: "POST",
  });
}

export function deletePaper(paperId: string): Promise<void> {
  return apiFetch<void>(`/api/papers/${paperId}`, { method: "DELETE" });
}

export function updatePaperDuration(
  paperId: string,
  minutes: number,
): Promise<QuestionPaper> {
  return apiFetch<QuestionPaper>(`/api/papers/${paperId}/duration`, {
    method: "PATCH",
    body: JSON.stringify({ default_duration_minutes: minutes }),
  });
}

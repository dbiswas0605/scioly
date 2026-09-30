import { apiFetch } from "@/lib/api/client";
import type { Question, QuestionUpdateInput } from "@/lib/api/types";

export function getQuestions(paperId: string): Promise<Question[]> {
  return apiFetch<Question[]>(`/api/papers/${paperId}/questions`, {
    cache: "no-store",
  });
}

export function updateQuestion(
  paperId: string,
  questionId: string,
  data: QuestionUpdateInput,
): Promise<Question> {
  return apiFetch<Question>(`/api/papers/${paperId}/questions/${questionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function confirmAllQuestions(paperId: string): Promise<Question[]> {
  return apiFetch<Question[]>(`/api/papers/${paperId}/questions/confirm-all`, {
    method: "POST",
  });
}

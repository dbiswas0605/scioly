import { API_BASE_URL, ApiError, NetworkError, apiFetch } from "@/lib/api/client";
import type { QuestionPaper } from "@/lib/api/types";

type ParseStreamEvent =
  | { type: "log"; message: string }
  | { type: "complete"; paper: QuestionPaper }
  | { type: "error"; message: string };

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

export async function parsePaperWithProgress(
  paperId: string,
  onLog: (message: string) => void,
): Promise<QuestionPaper> {
  const path = `/api/papers/${paperId}/parse/stream`;
  const url = `${API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { Accept: "application/x-ndjson" },
    });
  } catch (cause) {
    console.error(`[parsePaperWithProgress] network error calling ${url}:`, cause);
    throw new NetworkError(url, cause);
  }

  if (!response.ok) {
    let message = `Request to ${path} failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body && typeof body === "object" && "detail" in body) {
        message = String((body as { detail: unknown }).detail);
      }
    } catch {
      // The response wasn't JSON; use the status-based message.
    }
    throw new ApiError(response.status, message);
  }

  if (!response.body) {
    throw new Error("The server did not provide a readable progress stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: QuestionPaper | undefined;

  function handleLine(line: string) {
    if (!line.trim()) return;

    const event = JSON.parse(line) as ParseStreamEvent;
    if (event.type === "log") {
      onLog(event.message);
    } else if (event.type === "complete") {
      result = event.paper;
    } else if (event.type === "error") {
      throw new ApiError(502, event.message);
    } else {
      throw new Error("The server sent an unrecognized progress event.");
    }
  }

  try {
    while (true) {
      let chunk: ReadableStreamReadResult<Uint8Array>;
      try {
        chunk = await reader.read();
      } catch (cause) {
        console.error(`[parsePaperWithProgress] stream error from ${url}:`, cause);
        throw new NetworkError(url, cause);
      }

      const { done, value } = chunk;
      buffer += decoder.decode(value, { stream: !done });

      let newline = buffer.indexOf("\n");
      while (newline !== -1) {
        handleLine(buffer.slice(0, newline));
        buffer = buffer.slice(newline + 1);
        newline = buffer.indexOf("\n");
      }

      if (done) break;
    }

    if (buffer.trim()) handleLine(buffer);
  } finally {
    reader.releaseLock();
  }

  if (!result) {
    throw new Error("The server ended the progress stream without completing parsing.");
  }
  return result;
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

import { apiFetch } from "@/lib/api/client";
import type {
  LlmProvider,
  LlmProviderTestResult,
  LlmProviderUpdateInput,
} from "@/lib/api/types";

export function getLlmProviders(): Promise<LlmProvider[]> {
  return apiFetch<LlmProvider[]>("/api/admin/llm-providers", {
    cache: "no-store",
  });
}

export function updateLlmProvider(
  providerId: string,
  data: LlmProviderUpdateInput,
): Promise<LlmProvider> {
  return apiFetch<LlmProvider>(`/api/admin/llm-providers/${providerId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function testLlmProvider(providerId: string): Promise<LlmProviderTestResult> {
  return apiFetch<LlmProviderTestResult>(
    `/api/admin/llm-providers/${providerId}/test`,
    { method: "POST" },
  );
}

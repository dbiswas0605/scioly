export { cn } from "cn"

// Wall-clock time between starting and submitting an exam attempt.
// Returns null while still in progress (no submitted_at yet).
export function formatDuration(startedAt: string, submittedAt: string | null): string | null {
  if (!submittedAt) return null;
  const seconds = Math.max(
    0,
    Math.round((new Date(submittedAt).getTime() - new Date(startedAt).getTime()) / 1000),
  );
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
}

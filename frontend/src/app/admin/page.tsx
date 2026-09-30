import { Bot, FileStack, Timer } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";
import { getAppSettings, getLlmProviders } from "@/lib/api/admin";
import { getPapers } from "@/lib/api/papers";
import { getSubjects } from "@/lib/api/subjects";
import type { AppSetting, LlmProvider, QuestionPaper } from "@/lib/api/types";
import { AdminPapers } from "./AdminPapers";
import { LlmSettings } from "./LlmSettings";
import { TimerSettings } from "./TimerSettings";

export default async function AdminPage() {
  let subjectCount: number | null = null;
  let providers: LlmProvider[] = [];
  let providersError: string | null = null;
  let papers: QuestionPaper[] = [];
  let papersError: string | null = null;
  let settings: AppSetting[] = [];
  let settingsError: string | null = null;

  try {
    const subjects = await getSubjects();
    subjectCount = subjects.length;
  } catch {
    // Backend may be unreachable — the count is just a sanity check, so we
    // silently omit it rather than blocking the whole page.
    subjectCount = null;
  }

  try {
    providers = await getLlmProviders();
  } catch (error) {
    providersError = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  try {
    papers = await getPapers();
  } catch (error) {
    papersError = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  try {
    settings = await getAppSettings();
  } catch (error) {
    settingsError = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">
            Admin
          </h1>
          <p className="text-muted-foreground">
            Manage question papers, LLM settings, and exam timers.
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          {subjectCount === null
            ? "Subjects: unavailable"
            : `Subjects in database: ${subjectCount}`}
        </Badge>
      </div>

      <Card className="mb-6">
        <CardHeader className="gap-3">
          <div className="flex items-center justify-between">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="size-4.5" />
            </span>
          </div>
          <CardTitle className="text-lg">LLM Settings</CardTitle>
          <CardDescription>
            Configure Anthropic, OpenAI, Ollama, or MLX (via a local
            OpenAI-compatible server) as parsers for uploaded question
            papers. Enable any combination — they&apos;re tried in priority
            order, falling back automatically if one fails.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {providersError ? (
            <p className="text-sm text-destructive">{providersError}</p>
          ) : (
            <LlmSettings providers={providers} />
          )}
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader className="gap-3">
          <div className="flex items-center justify-between">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileStack className="size-4.5" />
            </span>
          </div>
          <CardTitle className="text-lg">Question Papers</CardTitle>
          <CardDescription>
            Delete any uploaded paper — published or not. This also deletes
            its questions and any student attempt history for it.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {papersError ? (
            <p className="text-sm text-destructive">{papersError}</p>
          ) : (
            <AdminPapers papers={papers} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex items-center justify-between">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Timer className="size-4.5" />
            </span>
          </div>
          <CardTitle className="text-lg">Timers</CardTitle>
          <CardDescription>
            Set the default countdown timer applied to new exam papers.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {settingsError ? (
            <p className="text-sm text-destructive">{settingsError}</p>
          ) : (
            <TimerSettings
              setting={settings.find((s) => s.key === "default_exam_duration_minutes")}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

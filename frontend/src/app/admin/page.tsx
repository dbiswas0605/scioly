import { Bot, Database, FileStack, MessageSquareText, Timer } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/api/client";
import { getAppSettings, getLlmProviders } from "@/lib/api/admin";
import { getPapers } from "@/lib/api/papers";
import { getSubjects } from "@/lib/api/subjects";
import type { AppSetting, LlmProvider, QuestionPaper } from "@/lib/api/types";
import { AdminPapers } from "./AdminPapers";
import { LlmSettings } from "./LlmSettings";
import { ParsePromptSettings } from "./ParsePromptSettings";
import { TimerSettings } from "./TimerSettings";

const DEFAULT_PARSE_SYSTEM_PROMPT =
  "You are an expert at digitizing Science Olympiad practice exams. You will be given the raw content of an uploaded question paper. Extract every question in the document, preserving the original question numbering and wording exactly. For each question, determine whether it is multiple-choice (mcq) or short-answer. For mcq questions, extract every answer option with its label (A, B, C, D, ...) and text.\n\n" +
  "For every mcq question set suggested_correct_option_labels to an array containing every correct option label. First check whether the source document itself indicates the correct option(s) (an answer key, marked/bolded answers, asterisks, etc.) and use that if present. Otherwise, work out the correct answer(s) using subject-matter knowledge and the question wording; if it says 'select all that apply' or equivalent, include every correct choice, otherwise include the single correct choice. Use an empty array only when genuinely ambiguous, malformed, or unanswerable even after reasoning — not merely because the source lacks an answer key.\n\n" +
  "For explanation_text: if the source includes a written explanation, copy it in. Otherwise, write a brief (1-3 sentence) explanation yourself justifying why the correct option(s) are right. Only leave it null if you couldn't determine a correct answer at all.\n\n" +
  "A parent/teacher will review and can correct every suggestion before anything is shown to students, so it's fine to commit to a best-effort answer rather than abstaining — but never fabricate options or question text that isn't in the source. Return every extracted question in the required structured output format. Include every field in the schema; use an empty array when there are no applicable option labels and null for nullable fields that do not apply.";

const DEFAULT_PARSE_USER_PROMPT =
  "This document is titled '{paper_title}'. Extract every question from it.";

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
            Configure Anthropic, OpenAI, Ollama, LM Studio, or MLX (via a
            local OpenAI-compatible server) as parsers for uploaded question
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
              <MessageSquareText className="size-4.5" />
            </span>
          </div>
          <CardTitle className="text-lg">LLM Parsing Prompts</CardTitle>
          <CardDescription>
            Edit the plain-text system instructions and user prompt sent to
            the LLM when parsing uploaded papers.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {settingsError ? (
            <p className="text-sm text-destructive">{settingsError}</p>
          ) : (
            <div className="flex flex-wrap gap-3">
              <ParsePromptSettings
                setting={settings.find(
                  (setting) =>
                    setting.key === "question_paper_parse_system_prompt",
                )}
                settingKey="question_paper_parse_system_prompt"
                defaultPrompt={DEFAULT_PARSE_SYSTEM_PROMPT}
                buttonLabel="Configure system prompt"
                dialogTitle="Question-paper system prompt"
                fieldLabel="System prompt"
                description="These plain-text instructions define how the LLM should interpret and extract an uploaded question paper."
                savedMessage="Saved. This system prompt will be used for future parses."
              />
              <ParsePromptSettings
                setting={settings.find(
                  (setting) =>
                    setting.key === "question_paper_parse_user_prompt",
                )}
                settingKey="question_paper_parse_user_prompt"
                defaultPrompt={DEFAULT_PARSE_USER_PROMPT}
                buttonLabel="Configure user prompt"
                dialogTitle="Question-paper user prompt"
                fieldLabel="User prompt"
                description='This plain-text prompt is sent with each paper. Use "{paper_title}" to insert its title.'
                savedMessage="Saved. This user prompt will be used for future parses."
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader className="gap-3">
          <div className="flex items-center justify-between">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Database className="size-4.5" />
            </span>
          </div>
          <CardTitle className="text-lg">Database Connection</CardTitle>
          <CardDescription>
            Choose the PostgreSQL database used by the app. Existing local
            database data remains intact when you switch.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            href="/admin/database"
            className={buttonVariants({ variant: "outline" })}
          >
            Configure database connection
          </Link>
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

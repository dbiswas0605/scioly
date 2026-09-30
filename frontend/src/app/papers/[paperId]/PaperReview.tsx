"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCheck, CheckCircle2, Loader2, Sparkles, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";
import { parsePaper, publishPaper } from "@/lib/api/papers";
import { confirmAllQuestions, getQuestions } from "@/lib/api/questions";
import type { Question, QuestionPaper } from "@/lib/api/types";
import { QuestionCard } from "./QuestionCard";

const STATUS_LABEL: Record<string, string> = {
  draft: "Uploaded — not parsed yet",
  pending_review: "Needs review",
  published: "Published",
  archived: "Archived",
};

export function PaperReview({
  paper: initialPaper,
  initialQuestions,
  subjectName,
}: {
  paper: QuestionPaper;
  initialQuestions: Question[];
  subjectName: string | null;
}) {
  const [paper, setPaper] = useState(initialPaper);
  const [questions, setQuestions] = useState(initialQuestions);
  const [parsing, setParsing] = useState(false);
  const [confirmingAll, setConfirmingAll] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const unreviewedCount = questions.filter((q) => !q.is_reviewed).length;
  const canPublish =
    questions.length > 0 && unreviewedCount === 0 && paper.status !== "published";

  async function handleParse() {
    setParsing(true);
    setActionError(null);
    try {
      const updatedPaper = await parsePaper(paper.id);
      const updatedQuestions = await getQuestions(paper.id);
      setPaper(updatedPaper);
      setQuestions(updatedQuestions);
    } catch (error) {
      setActionError(getErrorMessage(error, "Could not reach the server."));
    } finally {
      setParsing(false);
    }
  }

  async function handleConfirmAll() {
    setConfirmingAll(true);
    setActionError(null);
    try {
      const updatedQuestions = await confirmAllQuestions(paper.id);
      setQuestions(updatedQuestions);
    } catch (error) {
      setActionError(getErrorMessage(error, "Could not confirm all questions."));
    } finally {
      setConfirmingAll(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setActionError(null);
    try {
      const updatedPaper = await publishPaper(paper.id);
      setPaper(updatedPaper);
    } catch (error) {
      setActionError(getErrorMessage(error, "Could not reach the server."));
    } finally {
      setPublishing(false);
    }
  }

  function handleQuestionSaved(updated: Question) {
    setQuestions((prev) => prev.map((q) => (q.id === updated.id ? updated : q)));
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link href="/upload" className="hover:underline">
              Upload
            </Link>
            <span>/</span>
            <span>{subjectName ?? "Question paper"}</span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">{paper.title}</h1>
          <p className="text-muted-foreground">
            {paper.source_filename} · {questions.length} question
            {questions.length === 1 ? "" : "s"}
          </p>
        </div>
        <Badge
          variant={paper.status === "published" ? "default" : "secondary"}
          className="text-sm"
        >
          {STATUS_LABEL[paper.status] ?? paper.status}
        </Badge>
      </div>

      {actionError ? (
        <Card className="mb-6 border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Something went wrong
              </CardTitle>
              <CardDescription>{actionError}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : null}

      {questions.length === 0 ? (
        <Card className="border-dashed">
          <CardHeader className="items-center gap-3 text-center">
            <Sparkles className="size-8 text-muted-foreground" />
            <CardTitle className="text-base">Not parsed yet</CardTitle>
            <CardDescription>
              Send this document to the configured LLM to extract its
              questions and answer options.
            </CardDescription>
            <Button onClick={handleParse} disabled={parsing} className="mt-2 gap-2">
              {parsing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Sparkles className="size-4" />
              )}
              {parsing ? "Parsing…" : "Parse with AI"}
            </Button>
          </CardHeader>
        </Card>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/30 p-4">
            <p className="text-sm text-muted-foreground">
              {unreviewedCount === 0
                ? "Every question has been reviewed."
                : `${unreviewedCount} question${unreviewedCount === 1 ? "" : "s"} still need review.`}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleParse}
                disabled={parsing}
                className="gap-2"
              >
                {parsing ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Sparkles className="size-4" />
                )}
                Re-parse with AI
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleConfirmAll}
                disabled={confirmingAll || unreviewedCount === 0}
                className="gap-2"
              >
                {confirmingAll ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <CheckCheck className="size-4" />
                )}
                Save & Confirm All
              </Button>
              <Button
                size="sm"
                onClick={handlePublish}
                disabled={!canPublish || publishing}
                className="gap-2"
              >
                {publishing ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="size-4" />
                )}
                {paper.status === "published" ? "Published" : "Publish"}
              </Button>
            </div>
          </div>

          {questions.map((question) => (
            <QuestionCard
              key={question.id}
              paperId={paper.id}
              question={question}
              onSaved={handleQuestionSaved}
            />
          ))}
        </div>
      )}
    </div>
  );
}

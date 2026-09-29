"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Clock, Loader2, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { submitAttempt } from "@/lib/api/attempts";
import { getErrorMessage } from "@/lib/api/client";
import type {
  AnswerInput,
  AttemptReview,
  ExamAttemptSummary,
  ExamSession,
} from "@/lib/api/types";
import { AttemptReviewView } from "./AttemptReviewView";

interface DraftAnswer {
  selectedOptionId?: string;
  shortAnswerText?: string;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function ExamAttemptView({
  session,
  initialReview,
  previousAttempts,
}: {
  session: ExamSession;
  initialReview: AttemptReview | null;
  previousAttempts: ExamAttemptSummary[];
}) {
  const [review, setReview] = useState<AttemptReview | null>(initialReview);
  const [answers, setAnswers] = useState<Record<string, DraftAnswer>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittedRef = useRef(false);

  const deadlineMs = useMemo(
    () => new Date(session.started_at).getTime() + session.duration_minutes_snapshot * 60_000,
    [session.started_at, session.duration_minutes_snapshot],
  );
  const [remainingMs, setRemainingMs] = useState(() => deadlineMs - Date.now());

  const questions = useMemo(
    () => [...session.questions].sort((a, b) => a.question_number - b.question_number),
    [session.questions],
  );

  async function handleSubmit(reason: "submitted" | "timed_out") {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    setError(null);

    const answerInputs: AnswerInput[] = questions
      .map((question): AnswerInput | null => {
        const draft = answers[question.id];
        if (!draft) return null;
        if (question.question_type === "mcq" && draft.selectedOptionId) {
          return { question_id: question.id, selected_option_id: draft.selectedOptionId };
        }
        if (question.question_type === "short_answer" && draft.shortAnswerText?.trim()) {
          return { question_id: question.id, short_answer_text: draft.shortAnswerText.trim() };
        }
        return null;
      })
      .filter((a): a is AnswerInput => a !== null);

    try {
      const result = await submitAttempt(session.id, answerInputs, reason);
      setReview(result);
    } catch (err) {
      submittedRef.current = false;
      setError(getErrorMessage(err, "Could not submit the exam."));
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (review || session.status !== "in_progress") return;

    const tick = () => {
      const remaining = deadlineMs - Date.now();
      setRemainingMs(remaining);
      if (remaining <= 0) {
        handleSubmit("timed_out");
      }
    };

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [review, session.status, deadlineMs]);

  if (review) {
    return (
      <AttemptReviewView review={review} previousAttempts={previousAttempts} />
    );
  }

  const lowTime = remainingMs < 60_000;

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="sticky top-16 z-40 mb-8 flex items-center justify-between gap-4 rounded-lg border bg-background/95 p-4 backdrop-blur-lg">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{session.paper_title}</h1>
          <p className="text-sm text-muted-foreground">
            Attempt {session.attempt_number} · {questions.length} question
            {questions.length === 1 ? "" : "s"}
          </p>
        </div>
        <div
          className={`flex items-center gap-2 rounded-lg border px-3 py-2 font-mono text-lg font-semibold ${
            lowTime ? "border-destructive/40 text-destructive" : ""
          }`}
        >
          <Clock className="size-5" />
          {formatDuration(remainingMs)}
        </div>
      </div>

      {error ? (
        <Card className="mb-6 border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t submit
              </CardTitle>
              <CardDescription>{error}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : null}

      <div className="flex flex-col gap-5">
        {questions.map((question) => (
          <Card key={question.id}>
            <CardHeader>
              <CardTitle className="text-base">
                Question {question.question_number}
              </CardTitle>
              <CardDescription>{question.prompt_text}</CardDescription>
            </CardHeader>
            <CardContent>
              {question.question_type === "mcq" ? (
                <RadioGroup
                  value={answers[question.id]?.selectedOptionId ?? ""}
                  onValueChange={(value) =>
                    setAnswers((prev) => ({
                      ...prev,
                      [question.id]: { selectedOptionId: value ?? undefined },
                    }))
                  }
                  className="flex flex-col gap-3"
                >
                  {question.options.map((option) => (
                    <Label
                      key={option.id}
                      htmlFor={`${question.id}-${option.id}`}
                      className="flex cursor-pointer items-center gap-3 rounded-lg border p-3 has-[[data-checked]]:border-primary has-[[data-checked]]:bg-primary/5"
                    >
                      <RadioGroupItem value={option.id} id={`${question.id}-${option.id}`} />
                      <span className="text-sm font-medium">{option.option_label}.</span>
                      <span className="text-sm">{option.option_text}</span>
                    </Label>
                  ))}
                </RadioGroup>
              ) : (
                <Textarea
                  value={answers[question.id]?.shortAnswerText ?? ""}
                  onChange={(event) =>
                    setAnswers((prev) => ({
                      ...prev,
                      [question.id]: { shortAnswerText: event.target.value },
                    }))
                  }
                  placeholder="Type your answer…"
                  rows={3}
                />
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <Button
          size="lg"
          onClick={() => handleSubmit("submitted")}
          disabled={submitting}
          className="gap-2"
        >
          {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {submitting ? "Submitting…" : "Submit Exam"}
        </Button>
      </div>
    </div>
  );
}

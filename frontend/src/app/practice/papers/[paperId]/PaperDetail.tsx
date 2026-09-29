"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Clock, Loader2, RotateCcw, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getPaperAttempts, startAttempt } from "@/lib/api/attempts";
import { getErrorMessage } from "@/lib/api/client";
import { useStudentName } from "@/hooks/useStudentName";
import type { ExamAttemptSummary, QuestionPaper, Student } from "@/lib/api/types";

const STATUS_LABEL: Record<string, string> = {
  in_progress: "In progress",
  submitted: "Submitted",
  timed_out: "Timed out",
  abandoned: "Abandoned",
};

export function PaperDetail({
  paper,
  students,
  subjectName,
}: {
  paper: QuestionPaper;
  students: Student[];
  subjectName: string | null;
}) {
  const router = useRouter();
  const { studentName, setStudentName } = useStudentName();
  const [attempts, setAttempts] = useState<ExamAttemptSummary[]>([]);
  // Tracks which (trimmed) name `attempts` currently corresponds to, set
  // only inside the fetch's then/catch callbacks — lets `loadingAttempts`
  // below be a pure derived value instead of a separately-set state flag.
  const [checkedName, setCheckedName] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedName = studentName.trim();
  const loadingAttempts = trimmedName !== "" && checkedName !== trimmedName;

  useEffect(() => {
    let cancelled = false;
    const trimmed = studentName.trim();
    const match = trimmed
      ? students.find((s) => s.display_name.toLowerCase() === trimmed.toLowerCase())
      : undefined;

    const request = match
      ? getPaperAttempts(paper.id, match.id)
      : Promise.resolve<ExamAttemptSummary[]>([]);

    request
      .then((result) => {
        if (cancelled) return;
        setAttempts(result);
        setCheckedName(trimmed);
      })
      .catch(() => {
        if (cancelled) return;
        setAttempts([]);
        setCheckedName(trimmed);
      });

    return () => {
      cancelled = true;
    };
  }, [studentName, students, paper.id]);

  const inProgressAttempt = attempts.find((a) => a.status === "in_progress");

  async function handleTakeExam() {
    const trimmed = studentName.trim();
    if (!trimmed) {
      setError("Enter your name first.");
      return;
    }
    setStarting(true);
    setError(null);
    try {
      setStudentName(trimmed);
      const session = await startAttempt(paper.id, trimmed);
      router.push(`/practice/attempts/${session.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Could not start the exam."));
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">
          <Link href="/practice" className="hover:underline">
            Practice
          </Link>
          {subjectName ? (
            <>
              {" "}
              /{" "}
              <Link
                href={`/practice/subjects/${paper.subject_id}`}
                className="hover:underline"
              >
                {subjectName}
              </Link>
            </>
          ) : null}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">{paper.title}</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="size-4" />
          {paper.default_duration_minutes} minutes · {paper.total_questions} question
          {paper.total_questions === 1 ? "" : "s"}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Who&apos;s taking this?</CardTitle>
          <CardDescription>
            Enter your name so your score and attempt history can be tracked.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label htmlFor="student-name">Your name</Label>
            <Input
              id="student-name"
              value={studentName}
              onChange={(event) => setStudentName(event.target.value)}
              placeholder="e.g. Jordan"
              className="w-full sm:w-72"
            />
          </div>

          {loadingAttempts ? (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Checking past attempts…
            </p>
          ) : attempts.length > 0 ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium">Your past attempts</p>
              {attempts.map((attempt) => (
                <Link
                  key={attempt.id}
                  href={`/practice/attempts/${attempt.id}`}
                  className="flex items-center justify-between gap-3 rounded-lg border p-3 text-sm transition-colors hover:bg-accent"
                >
                  <span>Attempt {attempt.attempt_number}</span>
                  <span className="flex items-center gap-2">
                    {attempt.score !== null ? (
                      <span className="text-muted-foreground">
                        {attempt.score} / {attempt.max_score}
                      </span>
                    ) : null}
                    <Badge variant="outline">
                      {STATUS_LABEL[attempt.status] ?? attempt.status}
                    </Badge>
                  </span>
                </Link>
              ))}
            </div>
          ) : null}

          {error ? (
            <p className="flex items-center gap-2 text-sm text-destructive">
              <TriangleAlert className="size-4 shrink-0" />
              {error}
            </p>
          ) : null}

          {inProgressAttempt ? (
            <Button
              nativeButton={false}
              render={<Link href={`/practice/attempts/${inProgressAttempt.id}`} />}
              className="gap-2"
            >
              <Clock className="size-4" />
              Resume in-progress attempt
            </Button>
          ) : (
            <Button onClick={handleTakeExam} disabled={starting} className="gap-2">
              {starting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : attempts.length > 0 ? (
                <RotateCcw className="size-4" />
              ) : (
                <Clock className="size-4" />
              )}
              {starting
                ? "Starting…"
                : attempts.length > 0
                  ? "Retake Exam"
                  : "Take Exam"}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

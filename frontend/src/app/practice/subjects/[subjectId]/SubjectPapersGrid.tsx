"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, FileStack } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getStudentAttempts } from "@/lib/api/attempts";
import { getStudents } from "@/lib/api/students";
import { useStudentName } from "@/hooks/useStudentName";
import { cn } from "@/lib/utils";
import type { ExamAttemptSummary, QuestionPaper } from "@/lib/api/types";

function scoreBadgeClass(percent: number): string {
  if (percent >= 95) {
    return "border-emerald-500/30 bg-emerald-500/15 text-emerald-700 dark:text-emerald-400";
  }
  if (percent >= 90) {
    return "border-blue-500/30 bg-blue-500/15 text-blue-700 dark:text-blue-400";
  }
  return "border-amber-500/30 bg-amber-500/15 text-amber-700 dark:text-amber-400";
}

export function SubjectPapersGrid({ papers }: { papers: QuestionPaper[] }) {
  const { studentName } = useStudentName();
  const [latestByPaper, setLatestByPaper] = useState<Map<string, ExamAttemptSummary>>(
    new Map(),
  );

  useEffect(() => {
    let cancelled = false;
    const trimmed = studentName.trim();

    const request: Promise<ExamAttemptSummary[]> = trimmed
      ? getStudents().then((students) => {
          const match = students.find(
            (s) => s.display_name.toLowerCase() === trimmed.toLowerCase(),
          );
          return match ? getStudentAttempts(match.id) : [];
        })
      : Promise.resolve([]);

    request
      .then((attempts) => {
        if (cancelled) return;
        const scored = attempts.filter(
          (a) => (a.status === "submitted" || a.status === "timed_out") && a.score !== null,
        );
        const latest = new Map<string, ExamAttemptSummary>();
        for (const attempt of scored) {
          const current = latest.get(attempt.paper_id);
          if (!current || attempt.attempt_number > current.attempt_number) {
            latest.set(attempt.paper_id, attempt);
          }
        }
        setLatestByPaper(latest);
      })
      .catch(() => {
        if (!cancelled) setLatestByPaper(new Map());
      });

    return () => {
      cancelled = true;
    };
  }, [studentName]);

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {papers.map((paper) => {
        const attempt = latestByPaper.get(paper.id);
        const percent =
          attempt && attempt.score !== null && attempt.max_score
            ? Math.round((attempt.score / attempt.max_score) * 1000) / 10
            : null;

        return (
          <Link key={paper.id} href={`/practice/papers/${paper.id}`}>
            <Card className="h-full transition-all hover:-translate-y-0.5 hover:shadow-md">
              <CardHeader className="gap-2">
                <div className="flex items-center justify-between">
                  <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileStack className="size-4.5" />
                  </span>
                  <div className="flex items-center gap-1.5">
                    {percent !== null ? (
                      <>
                        <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
                        <Badge variant="outline" className={cn("text-xs", scoreBadgeClass(percent))}>
                          {percent}%
                        </Badge>
                      </>
                    ) : (
                      <Badge variant="outline">{paper.default_duration_minutes} min</Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="text-lg">{paper.title}</CardTitle>
                <CardDescription>
                  {paper.total_questions} question
                  {paper.total_questions === 1 ? "" : "s"}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}

import Link from "next/link";
import {
  CheckCircle2,
  Circle,
  Minus,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AttemptReview, ExamAttemptSummary } from "@/lib/api/types";

const STATUS_LABEL: Record<string, string> = {
  submitted: "Submitted",
  timed_out: "Timed out",
  abandoned: "Abandoned",
  in_progress: "In progress",
};

export function AttemptReviewView({
  review,
  previousAttempts,
}: {
  review: AttemptReview;
  previousAttempts: ExamAttemptSummary[];
}) {
  const score = review.score ?? 0;
  const maxScore = review.max_score ?? 0;
  const percent = maxScore > 0 ? Math.round((score / maxScore) * 100) : null;

  const mostRecentPrior =
    previousAttempts
      .filter((a) => a.score !== null && a.max_score !== null)
      .sort((a, b) => a.attempt_number - b.attempt_number)
      .at(-1) ?? null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{review.paper_title}</h1>
          <p className="text-muted-foreground">
            Attempt {review.attempt_number} · {STATUS_LABEL[review.status] ?? review.status}
          </p>
        </div>
        <Badge variant="outline" className="text-base">
          {score} / {maxScore}
          {percent !== null ? ` (${percent}%)` : ""}
        </Badge>
      </div>

      {mostRecentPrior ? (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Compared to your last attempt</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="text-muted-foreground">
                Attempt {mostRecentPrior.attempt_number}: {mostRecentPrior.score} /{" "}
                {mostRecentPrior.max_score}
              </span>
              <ComparisonIcon
                prev={Number(mostRecentPrior.score)}
                current={Number(review.score)}
              />
              <span className="font-medium">
                Attempt {review.attempt_number}: {review.score} / {review.max_score}
              </span>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-col gap-5">
        {review.answers.map((answer) => (
          <Card key={answer.question_id}>
            <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
              <div>
                <CardTitle className="text-base">
                  Question {answer.question_number}
                </CardTitle>
                <CardDescription>{answer.prompt_text}</CardDescription>
              </div>
              {answer.is_correct === true ? (
                <Badge className="shrink-0 gap-1">
                  <CheckCircle2 className="size-3.5" /> Correct
                </Badge>
              ) : answer.is_correct === false ? (
                <Badge variant="destructive" className="shrink-0 gap-1">
                  <XCircle className="size-3.5" /> Incorrect
                </Badge>
              ) : (
                <Badge variant="secondary" className="shrink-0">
                  Not auto-graded
                </Badge>
              )}
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {answer.question_type === "mcq" ? (
                <div className="flex flex-col gap-2">
                  {answer.options.map((option) => {
                    const isSelected = option.id === answer.selected_option_id;
                    const isCorrect = option.is_correct;
                    return (
                      <div
                        key={option.id}
                        className={cn(
                          "flex items-center gap-3 rounded-lg border p-3 text-sm",
                          isCorrect &&
                            "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
                          isSelected &&
                            !isCorrect &&
                            "border-destructive/40 bg-destructive/10 text-destructive",
                        )}
                      >
                        {isCorrect ? (
                          <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                        ) : isSelected ? (
                          <XCircle className="size-4 shrink-0 text-destructive" />
                        ) : (
                          <Circle className="size-4 shrink-0 text-muted-foreground/40" />
                        )}
                        <span className="font-medium">{option.option_label}.</span>
                        <span>{option.option_text}</span>
                        {isSelected ? (
                          <span className="ml-auto text-xs text-muted-foreground">
                            Your answer
                          </span>
                        ) : null}
                      </div>
                    );
                  })}
                  {!answer.selected_option_id ? (
                    <p className="text-xs text-muted-foreground">
                      You didn&apos;t answer this question.
                    </p>
                  ) : null}
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      Your answer
                    </p>
                    <p className="text-sm">{answer.short_answer_text || "Not answered"}</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      Model answer
                    </p>
                    <p className="text-sm">
                      {answer.short_answer_expected || "Not provided"}
                    </p>
                  </div>
                </div>
              )}

              <div className="rounded-lg border bg-muted/30 p-3">
                <p className="mb-1 text-xs font-medium text-muted-foreground">
                  Explanation
                </p>
                <p className="text-sm">
                  {answer.explanation_text ||
                    "No explanation was provided for this question."}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8">
        <Link href="/practice" className="text-sm text-muted-foreground hover:underline">
          Back to Practice
        </Link>
      </div>
    </div>
  );
}

function ComparisonIcon({ prev, current }: { prev: number; current: number }) {
  if (current > prev) {
    return <TrendingUp className="size-4 text-emerald-600 dark:text-emerald-400" />;
  }
  if (current < prev) {
    return <TrendingDown className="size-4 text-destructive" />;
  }
  return <Minus className="size-4 text-muted-foreground" />;
}

import { notFound } from "next/navigation";
import { TriangleAlert } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError, getErrorMessage } from "@/lib/api/client";
import { getPaper } from "@/lib/api/papers";
import { getQuestions } from "@/lib/api/questions";
import { getSubjects } from "@/lib/api/subjects";
import type { Question, QuestionPaper } from "@/lib/api/types";
import { PaperReview } from "./PaperReview";

export default async function PaperReviewPage({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;

  let paper: QuestionPaper | null = null;
  let questions: Question[] = [];
  let subjectName: string | null = null;
  let errorMessage: string | null = null;
  let isNotFound = false;

  try {
    const [paperResult, questionsResult, subjects] = await Promise.all([
      getPaper(paperId),
      getQuestions(paperId),
      getSubjects(),
    ]);
    paper = paperResult;
    questions = questionsResult;
    subjectName = subjects.find((s) => s.id === paperResult.subject_id)?.name ?? null;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      isNotFound = true;
    } else {
      errorMessage = getErrorMessage(error, "Could not reach the server — is the backend running?");
    }
  }

  if (isNotFound) {
    notFound();
  }

  if (errorMessage || !paper) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t load this question paper
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <PaperReview
      paper={paper}
      initialQuestions={questions}
      subjectName={subjectName}
    />
  );
}

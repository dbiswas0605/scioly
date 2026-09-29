import { notFound } from "next/navigation";
import { TriangleAlert } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getAttemptReview,
  getAttemptSession,
  getPaperAttempts,
} from "@/lib/api/attempts";
import { ApiError, getErrorMessage } from "@/lib/api/client";
import type { AttemptReview, ExamAttemptSummary, ExamSession } from "@/lib/api/types";
import { ExamAttemptView } from "./ExamAttemptView";

export default async function AttemptPage({
  params,
}: {
  params: Promise<{ attemptId: string }>;
}) {
  const { attemptId } = await params;

  let session: ExamSession | null = null;
  let review: AttemptReview | null = null;
  let previousAttempts: ExamAttemptSummary[] = [];
  let errorMessage: string | null = null;
  let isNotFound = false;

  try {
    session = await getAttemptSession(attemptId);
    if (session.status !== "in_progress") {
      review = await getAttemptReview(attemptId);
    }
    const allAttempts = await getPaperAttempts(session.paper_id, session.student_id);
    previousAttempts = allAttempts.filter((a) => a.id !== attemptId);
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

  if (errorMessage || !session) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t load this attempt
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <ExamAttemptView
      session={session}
      initialReview={review}
      previousAttempts={previousAttempts}
    />
  );
}

import Link from "next/link";
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
import { getStudents } from "@/lib/api/students";
import { getSubjects } from "@/lib/api/subjects";
import type { QuestionPaper, Student } from "@/lib/api/types";
import { PaperDetail } from "./PaperDetail";

export default async function PaperDetailPage({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;

  let errorMessage: string | null = null;
  let isNotFound = false;
  let data: { paper: QuestionPaper; students: Student[]; subjectName: string | null } | null =
    null;

  try {
    const [paper, students, subjects] = await Promise.all([
      getPaper(paperId),
      getStudents(),
      getSubjects(),
    ]);

    if (paper.status !== "published") {
      isNotFound = true;
    } else {
      const subjectName = subjects.find((s) => s.id === paper.subject_id)?.name ?? null;
      data = { paper, students, subjectName };
    }
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

  if (data) {
    return (
      <PaperDetail
        paper={data.paper}
        students={data.students}
        subjectName={data.subjectName}
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <Card className="border-destructive/30 bg-destructive/5">
        <CardHeader className="flex-row items-start gap-3 space-y-0">
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
          <div className="flex flex-col gap-1">
            <CardTitle className="text-base text-destructive">
              Couldn&apos;t load this paper
            </CardTitle>
            <CardDescription>{errorMessage}</CardDescription>
          </div>
        </CardHeader>
      </Card>
      <p className="mt-4 text-sm text-muted-foreground">
        <Link href="/practice" className="hover:underline">
          Back to Practice
        </Link>
      </p>
    </div>
  );
}

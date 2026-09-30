import Link from "next/link";
import { notFound } from "next/navigation";
import { FileStack, TriangleAlert } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";
import { getPapers } from "@/lib/api/papers";
import { getSubjects } from "@/lib/api/subjects";
import { SubjectPapersGrid } from "./SubjectPapersGrid";

export default async function SubjectPapersPage({
  params,
}: {
  params: Promise<{ subjectId: string }>;
}) {
  const { subjectId } = await params;

  let subjectName: string | null = null;
  let publishedPapers: Awaited<ReturnType<typeof getPapers>> = [];
  let errorMessage: string | null = null;

  try {
    const [subjects, papers] = await Promise.all([getSubjects(), getPapers()]);
    const subject = subjects.find((s) => s.id === subjectId);
    if (!subject) {
      notFound();
    }
    subjectName = subject.name;
    publishedPapers = papers.filter(
      (p) => p.subject_id === subjectId && p.status === "published",
    );
  } catch (error) {
    errorMessage = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">
          <Link href="/practice" className="hover:underline">
            Practice
          </Link>
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          {subjectName ?? "Practice papers"}
        </h1>
        <p className="text-muted-foreground">
          Pick a paper below to take a new attempt or review a past one.
        </p>
      </div>

      {errorMessage ? (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t load papers
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : publishedPapers.length === 0 ? (
        <Card className="border-dashed">
          <CardHeader className="items-center gap-2 text-center">
            <FileStack className="size-8 text-muted-foreground" />
            <CardTitle className="text-base">No papers published yet</CardTitle>
            <CardDescription>
              Once a parent or teacher publishes a paper for this subject,
              it&apos;ll show up here.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <SubjectPapersGrid papers={publishedPapers} />
      )}
    </div>
  );
}

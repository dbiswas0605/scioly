import Link from "next/link";
import { BarChart3, FileStack, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";
import { getPapers } from "@/lib/api/papers";
import { getSubjects } from "@/lib/api/subjects";
import type { QuestionPaper, Subject } from "@/lib/api/types";
import { UploadForm } from "./UploadForm";

const STATUS_LABEL: Record<string, string> = {
  draft: "Uploaded — not parsed",
  pending_review: "Needs review",
  published: "Published",
  archived: "Archived",
};

const STATUS_VARIANT: Record<
  string,
  "default" | "secondary" | "outline" | "destructive"
> = {
  draft: "outline",
  pending_review: "secondary",
  published: "default",
  archived: "outline",
};

export default async function UploadPage() {
  let subjects: Subject[] = [];
  let papers: QuestionPaper[] = [];
  let errorMessage: string | null = null;

  try {
    [subjects, papers] = await Promise.all([getSubjects(), getPapers()]);
  } catch (error) {
    errorMessage = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">
            Upload a Question Paper
          </h1>
          <p className="text-muted-foreground">
            Parents and teachers can upload a new question paper here. The
            paper will be parsed by an LLM and reviewed before it&apos;s saved.
          </p>
        </div>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/upload/reports" />}
          className="gap-2"
        >
          <BarChart3 className="size-4" />
          Reports
        </Button>
      </div>

      {errorMessage ? (
        <Card className="mb-6 border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t reach the server
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : null}

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>New question paper</CardTitle>
          <CardDescription>
            Upload a file, then you&apos;ll review the AI-parsed questions
            before it&apos;s published for students.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadForm subjects={subjects} />
        </CardContent>
      </Card>

      {papers.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Your question papers</CardTitle>
            <CardDescription>
              Resume a review, or check on a paper you&apos;ve already published.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {papers.map((paper) => (
              <Link
                key={paper.id}
                href={`/papers/${paper.id}`}
                className="flex items-center justify-between gap-3 rounded-lg border p-3 transition-colors hover:bg-accent"
              >
                <div className="flex items-center gap-3">
                  <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileStack className="size-4" />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{paper.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {paper.total_questions ?? 0} question
                      {paper.total_questions === 1 ? "" : "s"}
                    </span>
                  </div>
                </div>
                <Badge variant={STATUS_VARIANT[paper.status] ?? "outline"}>
                  {STATUS_LABEL[paper.status] ?? paper.status}
                </Badge>
              </Link>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

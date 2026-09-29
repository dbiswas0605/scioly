import Link from "next/link";
import { BookOpen, TriangleAlert } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getErrorMessage } from "@/lib/api/client";
import { getSubjects } from "@/lib/api/subjects";
import type { Subject } from "@/lib/api/types";

export default async function PracticePage() {
  let subjects: Subject[] = [];
  let errorMessage: string | null = null;

  try {
    subjects = await getSubjects();
  } catch (error) {
    errorMessage = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Practice Exams
        </h1>
        <p className="text-muted-foreground">
          Pick a subject below to start a new practice paper or revisit one
          you&apos;ve already taken.
        </p>
      </div>

      {errorMessage ? (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t load subjects
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : subjects.length === 0 ? (
        <Card className="border-dashed">
          <CardHeader className="items-center gap-2 text-center">
            <BookOpen className="size-8 text-muted-foreground" />
            <CardTitle className="text-base">No subjects yet</CardTitle>
            <CardDescription>
              Once a parent or teacher uploads a question paper, its subject
              will show up here.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((subject) => (
            <Link key={subject.id} href={`/practice/subjects/${subject.id}`}>
              <Card className="h-full transition-all hover:-translate-y-0.5 hover:shadow-md">
                <CardHeader className="gap-2">
                  <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <BookOpen className="size-4.5" />
                  </span>
                  <CardTitle className="text-lg">{subject.name}</CardTitle>
                  <CardDescription>
                    Practice papers for {subject.name}.
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

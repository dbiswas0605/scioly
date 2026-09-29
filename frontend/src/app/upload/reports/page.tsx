import Link from "next/link";
import { ClipboardList, Minus, TrendingDown, TrendingUp, TriangleAlert, Users } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getErrorMessage } from "@/lib/api/client";
import { getAttemptReports, getStudentOverviews } from "@/lib/api/reports";
import type { AttemptPoint, StudentOverview, StudentPaperReport } from "@/lib/api/types";
import { TrendChart } from "./TrendChart";

function formatDate(value: string | null): string {
  if (!value) return "Never";
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function DeltaIndicator({ attempts }: { attempts: AttemptPoint[] }) {
  const first = attempts[0].percent;
  const last = attempts[attempts.length - 1].percent;
  if (first === null || last === null) return null;
  const diff = Math.round((last - first) * 10) / 10;

  if (diff > 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
        <TrendingUp className="size-3.5" />+{diff}% since first attempt
      </span>
    );
  }
  if (diff < 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-destructive">
        <TrendingDown className="size-3.5" />
        {diff}% since first attempt
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      <Minus className="size-3.5" />
      No change since first attempt
    </span>
  );
}

export default async function ReportsPage() {
  let overviews: StudentOverview[] = [];
  let paperReports: StudentPaperReport[] = [];
  let errorMessage: string | null = null;

  try {
    [overviews, paperReports] = await Promise.all([
      getStudentOverviews(),
      getAttemptReports(),
    ]);
  } catch (error) {
    errorMessage = getErrorMessage(error, "Could not reach the server — is the backend running?");
  }

  const totalAttempts = overviews.reduce((sum, o) => sum + o.total_attempts, 0);
  const scored = overviews.filter((o) => o.average_percent !== null);
  const overallAverage =
    scored.length > 0
      ? Math.round(
          (scored.reduce((sum, o) => sum + (o.average_percent ?? 0), 0) / scored.length) * 10,
        ) / 10
      : null;

  const reportsByStudent = new Map<string, StudentPaperReport[]>();
  for (const report of paperReports) {
    const existing = reportsByStudent.get(report.student_id);
    if (existing) {
      existing.push(report);
    } else {
      reportsByStudent.set(report.student_id, [report]);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">
          <Link href="/upload" className="hover:underline">
            Upload
          </Link>
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Reports</h1>
        <p className="text-muted-foreground">
          Student exam history, scores, and trends across retakes.
        </p>
      </div>

      {errorMessage ? (
        <Card className="mb-6 border-destructive/30 bg-destructive/5">
          <CardHeader className="flex-row items-start gap-3 space-y-0">
            <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" />
            <div className="flex flex-col gap-1">
              <CardTitle className="text-base text-destructive">
                Couldn&apos;t load reports
              </CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : overviews.length === 0 ? (
        <Card className="border-dashed">
          <CardHeader className="items-center gap-2 text-center">
            <ClipboardList className="size-8 text-muted-foreground" />
            <CardTitle className="text-base">No exam attempts yet</CardTitle>
            <CardDescription>
              Once a student takes a practice exam, their scores and trends will
              show up here.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="gap-1">
                <CardDescription>Students</CardDescription>
                <CardTitle className="text-2xl">{overviews.length}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="gap-1">
                <CardDescription>Total attempts</CardDescription>
                <CardTitle className="text-2xl">{totalAttempts}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="gap-1">
                <CardDescription>Average score</CardDescription>
                <CardTitle className="text-2xl">
                  {overallAverage !== null ? `${overallAverage}%` : "—"}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="text-lg">Students</CardTitle>
              <CardDescription>Overall activity per student.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {overviews.map((o) => (
                <div
                  key={o.student_id}
                  className="flex items-center justify-between gap-3 rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Users className="size-4" />
                    </span>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{o.student_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {o.total_attempts} attempt{o.total_attempts === 1 ? "" : "s"} ·{" "}
                        {o.papers_attempted} paper{o.papers_attempted === 1 ? "" : "s"} ·
                        last activity {formatDate(o.last_activity)}
                      </span>
                    </div>
                  </div>
                  <Badge variant="outline">
                    {o.average_percent !== null ? `${o.average_percent}% avg` : "Not scored"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="flex flex-col gap-8">
            {[...reportsByStudent.entries()].map(([studentId, reports]) => (
              <div key={studentId} className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold tracking-tight">
                  {reports[0].student_name}
                </h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  {reports.map((report) => {
                    const latest = report.attempts[report.attempts.length - 1];
                    return (
                      <Card key={report.paper_id}>
                        <CardHeader className="gap-1">
                          <div className="flex items-center justify-between gap-2">
                            <CardTitle className="text-base">{report.paper_title}</CardTitle>
                            <Badge variant="outline">{report.subject_name}</Badge>
                          </div>
                          <CardDescription>
                            {report.attempts.length} attempt
                            {report.attempts.length === 1 ? "" : "s"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-2">
                          {report.attempts.length >= 2 ? (
                            <>
                              <TrendChart attempts={report.attempts} />
                              <DeltaIndicator attempts={report.attempts} />
                            </>
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              Scored {latest.percent ?? 0}% ({latest.score ?? 0}/
                              {latest.max_score ?? 0} pts) — retake to see a trend here.
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

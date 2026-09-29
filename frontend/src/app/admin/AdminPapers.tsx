"use client";

import { useState } from "react";
import { FileStack, Loader2, Trash2 } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/api/client";
import { deletePaper } from "@/lib/api/papers";
import type { QuestionPaper } from "@/lib/api/types";

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
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

export function AdminPapers({ papers: initialPapers }: { papers: QuestionPaper[] }) {
  const [papers, setPapers] = useState(initialPapers);
  const [pendingDelete, setPendingDelete] = useState<QuestionPaper | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirmDelete() {
    if (!pendingDelete) return;
    const paperId = pendingDelete.id;
    setDeleting(true);
    setError(null);
    try {
      await deletePaper(paperId);
      setPapers((prev) => prev.filter((p) => p.id !== paperId));
      setPendingDelete(null);
    } catch (err) {
      setError(getErrorMessage(err, "Could not delete this paper."));
    } finally {
      setDeleting(false);
    }
  }

  if (papers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No question papers uploaded yet.</p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {papers.map((paper) => (
        <div
          key={paper.id}
          className="flex items-center justify-between gap-3 rounded-lg border p-3"
        >
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileStack className="size-4" />
            </span>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{paper.title}</span>
              <span className="text-xs text-muted-foreground">
                {paper.subject_name ?? "Unknown subject"} · {paper.total_questions ?? 0}{" "}
                question{paper.total_questions === 1 ? "" : "s"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_VARIANT[paper.status] ?? "outline"}>
              {STATUS_LABEL[paper.status] ?? paper.status}
            </Badge>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-destructive"
              onClick={() => {
                setError(null);
                setPendingDelete(paper);
              }}
            >
              <Trash2 className="size-4" />
            </Button>
          </div>
        </div>
      ))}

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) setPendingDelete(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete &quot;{pendingDelete?.title}&quot;?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This permanently deletes the paper, its questions, and any student
              attempt history for it
              {pendingDelete?.status === "published"
                ? " — including for a published exam students may have taken"
                : ""}
              . This can&apos;t be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              type="button"
              variant="destructive"
              disabled={deleting}
              onClick={confirmDelete}
              className="gap-2"
            >
              {deleting ? <Loader2 className="size-4 animate-spin" /> : null}
              {deleting ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
